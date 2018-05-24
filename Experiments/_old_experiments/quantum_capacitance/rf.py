import time
from collections import OrderedDict
import numpy as np

from qcodes.instrument_drivers.AlazarTech.acq_controllers import ATS9360Controller

from pulsar.awg import awg5014

from stationq.qctools import instruments as instools
from stationq.data.data_storage import Data, GridData
from stationq.experiment.measurement import Parameter, BaseMeasurement, PysweepGrid
from stationq.experiment.ATS import AlazarMeasurement

import logging
logger = logging.getLogger('measurement')


class AlazarMeasurementExt(AlazarMeasurement):
    pass

    # def setup(self):
    #     super().setup()

    #     self.alazar_axes = OrderedDict({})
    #     if not self.ats_integrate_samples():
    #         self.alazar_axes['Times (s)'] = {
    #             'value' : np.arange(self.samples_per_record)/self.station.alazar.sample_rate.get(),
    #             'unit' : 's',
    #         }

    #     if not self.ats_average_records():
    #         self.alazar_axes['Records'] = {
    #             'value' : np.arange(self.ats_records_per_buffer.get())
    #         }

    #     if not self.ats_average_buffers():
    #         self.alazar_axes['Buffers'] = {
    #             'value' : np.arange(self.ats_buffers_per_acquisition.get())
    #         }

# class Reflectometry(AlazarMeasurementExt):

#     def __init__(self, *arg, **kw):
#         super().__init__(*arg, **kw)

#         self.ats_demod(True)
#         self.ats_integrate_samples(True)


#     def setup(self):
#         super().setup()
#         self.station.LO.frequency(self.station.RF.frequency() + self.IF())
#         self.setup_alazar()


#     def measure_datapoint(self, station, namespace):
#         A, B = self.acquire()

#         inner_axes = {k : {'value' : v, 'independent_parameter' : True} for k, v in self.alazar_axes}
#         grids = np.meshgrid(*[v for k, v in self.alazar_axes])
#         for i, k in enumerate(inner_axes):
#             inner_axes[k]['value'] = grids[i]

#         ret = OrderedDict({
#             "chanA_I" : {"unit" : "V", "value" : A.real},
#             "chanA_Q" : {"unit" : "V", "value" : A.imag},
#             "chanB_I" : {"unit" : "V", "value" : B.real},
#             "chanB_Q" : {"unit" : "V", "value" : B.imag},
#             "chanA_abs" : {"unit" : "V", "value" : abs(A), },
#             "chanB_abs" : {"unit" : "V", "value" : abs(B), },
#             "chanA_phase" : {"unit" : "deg", "value" : phiA},
#             "chanB_phase" : {"unit" : "deg", "value" : phiB },
#             "delta_phase" : {"unit" : "deg", "value" : dphi },
#             "abs" : {"unit" : "V", "value" : (abs(A)**2 + abs(B)**2)**.5, },
#         })

#         for k, v in full_axes.items():
#             ret[k] = v

#         return ret


class AWGMeasurement(BaseMeasurement):

    def __init__(self, *arg, **kw):
        super().__init__(*arg, **kw)
        self.awghandler = awg5014.AWG5014Handler(self.station.awg)
        self.do_setup_awg = True

    def awg_sequence(self):
        raise NotImplementedError

    def setup_awg(self):
        self.awghandler.awg_settings.update(self.namespace.awg_settings)
        self.awghandler.program_awg(self.awg_sequence())

        for i in range(1,5):
            self.station.awg.set(f"ch{i}_state", 1)

        self.station.awg.start()
        time.sleep(0.1)

        nretry = 0
        while self.station.awg.state() != 'Waiting for trigger':
            logger.info('Waiting for AWG to get ready...')
            if nretry > 3:
                raise RuntimeError(f'AWG not started after {nretry} seconds.')
            time.sleep(1)

    def setup(self):
        super().setup()
        if self.do_setup_awg:
            self.setup_awg()


class SimpleAWGRamp(AWGMeasurement):

    def __init__(self, *arg, **kw):
        super().__init__(*arg, **kw)

        self.add_parameter('ramp_pts', Parameter, initial_value=11)
        self.add_parameter('max_val', Parameter, initial_value=0.1)
        self.add_parameter('val_len', Parameter, initial_value=1e-7)
        self.add_parameter('ramp_down_len', Parameter, initial_value=1e-6)
        self.add_parameter('awg_chan', Parameter, initial_value=2)

    def awg_sequence(self):
        h = self.awghandler
        chan = self.awg_chan()

        samples_per_val = h.time_to_samples(self.val_len())
        samples_ramp_down = h.time_to_samples(self.ramp_down_len())
        vals = np.linspace(0, h.voltage_to_wfscale()[self.awg_chan()-1] * self.max_val(), self.ramp_pts())

        wf = np.zeros((self.ramp_pts()*samples_per_val+samples_ramp_down,),
                      dtype=h.get_awg_wf_dtype(chans=[chan]))

        for i, v in enumerate(vals):
            idx0, idx1 = i*samples_per_val, (i+1)*samples_per_val
            wf[f'ch{chan}_wf'][idx0:idx1] = v
            wf[f'ch{chan}_m1'][idx0+1:idx0+2] = 1
        wf[f'ch{chan}_wf'][idx1:] = np.linspace(v, 0, samples_ramp_down)

        return [dict(wf=wf)]


class AWG2DRamp(AWGMeasurement):

    trigger_chan = 'ch2_m1'
    ramp_chan = (2, 1)
    ramp_pts = (3, 3)
    ramp_min = (0, 0)
    ramp_max = (1, 0.1)
    ramp_elt_len = 10e-6
    ramp_down_len = 1e-3
    line_reps = 1

    def awg_sequence(self):
        h = self.awghandler

        chans = list(self.ramp_chan)
        if int(self.trigger_chan[2]) not in chans:
            chans.append(int(self.trigger_chan[2]))
        chans.sort()

        dt = h.get_awg_wf_dtype(chans=chans)
        samples_per_val = int(h.time_to_samples(self.ramp_elt_len))
        samples_down = h.time_to_samples(self.ramp_down_len)
        samples_per_line = samples_per_val * self.ramp_pts[0] + samples_down

        wfs = []
        for i, v in enumerate(np.linspace(h.voltage_to_wfscale()[self.ramp_chan[1]-1] * self.ramp_min[1],
                                          h.voltage_to_wfscale()[self.ramp_chan[1]-1] * self.ramp_max[1],
                                          self.ramp_pts[1])):
            wf = np.zeros(samples_per_line, dtype=dt)

            for j, w in enumerate(np.linspace(h.voltage_to_wfscale()[self.ramp_chan[0]-1] * self.ramp_min[0],
                                              h.voltage_to_wfscale()[self.ramp_chan[0]-1] * self.ramp_max[0],
                                              self.ramp_pts[0])):
                wf[f'ch{self.ramp_chan[0]}_wf'][j*samples_per_val:(j+1)*samples_per_val] = w
                wf[f'{self.trigger_chan}'][j*samples_per_val+1:j*samples_per_val+3] = 1

            dn = np.linspace(h.voltage_to_wfscale()[self.ramp_chan[0]-1] * self.ramp_max[0],
                             h.voltage_to_wfscale()[self.ramp_chan[0]-1] * self.ramp_min[0],
                             samples_down)

            wf[f'ch{self.ramp_chan[0]}_wf'][-samples_down:] = dn
            wf[f'ch{self.ramp_chan[1]}_wf'][:] = v

            wfs.append(dict(wf=wf, name=f'wf_{i}', nreps=self.line_reps, trigger_wait=1))

        # ramp outer value down as well
        wf = np.zeros(samples_per_line, dtype=dt)
        dn = np.linspace(h.voltage_to_wfscale()[self.ramp_chan[1]-1] * self.ramp_max[1],
                         h.voltage_to_wfscale()[self.ramp_chan[1]-1] * self.ramp_min[1],
                         samples_per_line)
        wf[f'ch{self.ramp_chan[1]}_wf'][:] = dn
        wfs.append(dict(wf=wf, name=f'wf_{i+1}'))

        return wfs


# class AWGGateSweep(SimpleAWGRamp, Reflectometry, PysweepGrid):

#     controller_cls = TrigController

#     def __init__(self, *arg, **kw):
#         super().__init__(*arg, **kw)
#         self.ats_average_records(False)

#     def setup(self):
#         # setting up basic triggering
#         self.controller_cls.fg = self.station.fg
#         self.station.fg.ch1_output_enabled(False)

#         # setting up alazar
#         # first determine how long we integrate, and if we can fit more integration time into
#         # the time of a record
#         self.ats_records_per_buffer(self.ramp_pts())
#         self.setup_alazar()

#         # TODO: can this go into the alazar class?
#         # idea: we interpret integration time as the minimal one, and then see
#         # how much time a record will actually take. then adjust.
#         logger.info(f'Samples per record: {self.samples_per_record}')
#         rectime = self.samples_per_record / float(self.namespace.ats_settings['sample_rate'])
#         # if rectime - self.ats_int_time() > 1e-6:
#         #     old_int_time = self.ats_int_time()
#         #     self.ats_int_time((rectime - 1e-6)//(1./self.IF()) * 1./self.IF())
#         #     self.setup_alazar()
#         # logger.info(f'Updated integration time: {self.ats_int_time()}')
#         # logger.info(f'Updated samples per record: {self.samples_per_record}')

#         # time per gate voltage setting is a little longer than the record time
#         vlen = (rectime//10e-6 + 1) * 10e-6
#         self.val_len(vlen)
#         logger.info(f'Time per gate voltage: {vlen} s')

#         linetime = vlen * self.ramp_pts() + self.ramp_down_len()
#         logger.info(f'Time per AWG sweep: {linetime} s')

#         super().setup()

#     def cleanup(self):
#         self.station.fg.ch1_output_enabled(False)

