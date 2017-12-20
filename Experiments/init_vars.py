class NameSpace:
    pass

namespace = NameSpace()

namespace.ats_settings = dict(
    clock_source='INTERNAL_CLOCK',
    sample_rate=int(1e9),
    clock_edge='CLOCK_EDGE_RISING',
    decimation=1,
    coupling=['DC','DC'],
    channel_range=[.4, .4],
    impedance=[50, 50],
    trigger_operation='TRIG_ENGINE_OP_J',
    trigger_engine1='TRIG_ENGINE_J',
    trigger_source1='CHANNEL_A',
    trigger_slope1='TRIG_SLOPE_POSITIVE',
    trigger_level1=128+3,
    trigger_engine2='TRIG_ENGINE_K',
    trigger_source2='DISABLE',
    trigger_slope2='TRIG_SLOPE_POSITIVE',
    trigger_level2=128,
    external_trigger_coupling='DC',
    external_trigger_range='ETR_2V5',
    trigger_delay=0,
    timeout_ticks=0,
    aux_io_mode='AUX_IN_AUXILIARY',
    aux_io_param='NONE'
)
