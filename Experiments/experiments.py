# -*- coding: utf-8 -*-

import numpy as np

from init import *
from quantum_capacitance.rf import AWGMeasurement

### Definitions

class AWG2DRamp(AWGMeasurement):
    
    trigger_chan = 'ch2_m1'
    ramp_chan = (2, 1)
    ramp_pts = (3, 3)
    ramp_min = (0, 0)
    ramp_max = (1, 0.1)
    ramp_elt_len = 10e-6
    ramp_down_len = 1e-3
    
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
                wf[f'{self.trigger_chan}'][j*samples_per_val+1:j*samples_per_val+2] = 1
            
            dn = np.linspace(h.voltage_to_wfscale()[self.ramp_chan[0]-1] * self.ramp_max[0], 
                             h.voltage_to_wfscale()[self.ramp_chan[0]-1] * self.ramp_min[0], 
                             samples_down)
            
            wf[f'ch{self.ramp_chan[0]}_wf'][-samples_down:] = dn
            wf[f'ch{self.ramp_chan[1]}_wf'][:] = v
            
            wfs.append(dict(wf=wf, name=f'wf_{i}'))
            
        # ramp outer value down as well
        wf = np.zeros(samples_down, dtype=dt)
        dn = np.linspace(h.voltage_to_wfscale()[self.ramp_chan[1]-1] * self.ramp_max[1], 
                         h.voltage_to_wfscale()[self.ramp_chan[1]-1] * self.ramp_min[1], 
                         samples_down)
        wf[f'ch{self.ramp_chan[1]}_wf'][:] = dn
        wfs.append(dict(wf=wf, name=f'wf_{i+1}'))
        
        return wfs
    



### Settings
namespace.ats_settings['sample_rate'] = int(1e8)
namespace.ats_settings['trigger_source1'] = 'EXTERNAL'
namespace.awg_settings['sampling_rate'] = int(1e7)
namespace.awg_settings['channel_1']['analog_amplitude'] = 0.2
namespace.awg_settings['channel_2']['analog_amplitude'] = 0.2
fg.ch1_frequency(50)
fg.ch1_output_enabled(False)

if 1: # Test: Program 2D ramp on AWG
    r = AWG2DRamp(station, namespace)
    r.trigger_src = fg
    r.trigger_chan = 'ch2_m1'
    r.ramp_chan = (2, 1)
    r.ramp_pts = (101, 101)
    r.ramp_min = (0, 0)
    r.ramp_max = (0.1, 0.1)
    r.ramp_elt_len = 85e-6
    r.ramp_down_len = 100e-6
    r.setup()
    
    