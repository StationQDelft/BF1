from stationq.experiment.ATS import AlzTimeTrace

namespace.ats_settings['sample_rate'] = 1e9
namespace.ats_settings['trigger_source1'] = 'CHANNEL_A'

m = AlzTimeTrace(station, namespace)
m.run()

fig, ax = plt.subplots(1,1)
ax.plot(m.data['A']['time [us]'].reshape(-1), m.data['A']['A [V]'].reshape(-1))
ax.set_xlabel('time [us]')
ax.set_ylabel('chan A [V]')
ax.set_title(m.datafilepath, size='small')
plt.show()
