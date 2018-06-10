'''

'''
import logging
import os
import socket

import emews.base.config
import emews.base.importclass

def system_init(args):
    '''
    Inits the eMews daemon.
    '''
    # first thing we need to do is parse the configs
    # base system conf (non-user config - global)
    base_config = emews.base.config.parse("conf.yml")  # conf.yml in same directory as this
    # system conf (user config - global)
    system_config = emews.base.config.parse(os.path.join("..", "system.yml")) \
        if args.sys_config is None else emews.base.config.parse(args.sys_config)
    # node conf (user config - per node)
    node_config = emews.base.config.parse(args.node_config)

    # get the node name
    node_name = _get_node_name(system_config['general'], node_config.get('general', {}),
                               args.node_name)
    # init the logger
    logger = logging.LoggerAdapter(
        _init_base_logger(base_config['logging'], system_config['logging'], node_config['logging']),
        {'nodename': node_name})

    # now we have logging, so we can start outputting though the logger
    logger.debug("Logger initialized.")

    # setup the config object
    config_start_dict = dict()
    config_start_dict['config'] = _merge_configs(base_config, system_config, node_config)
    config_start_dict['system_options'] = SystemOptions(node_name=node_name, logger=logger)

    config_start = emews.base.config.Config(config_start_dict)
    return emews.base.system_manager.SystemManager(config_start)

def _get_node_name(system_config, node_config, arg_name):
    '''
    Determines the node name.
    '''
    # command line arg (top precedence)
    if arg_name is not None:
        return arg_name

    # then node config
    node_name = node_config.get('node_name', None)
    if node_name is not None:
        return node_name

    # then system config
    node_name = system_config.get('node_name', None)
    if node_name is not None:
        return node_name

    # default: use host name
    return socket.gethostname()

def _init_base_logger(base_config, system_config, node_config):
    '''
    Sets up the logger.
    '''
    logger_type = system_config.get('logger', base_config['logger'])
    message_level = system_config.get('message_level', base_config['message_level'])

    logger = logging.getLogger(logger_type)
    logger.setLevel(message_level)
    logger.propagate(False)

    for handler_class_path in base_config['log_types'][logger_type]['handlers']:
        handler_class = emews.base.importclass.import_class_from_module(handler_class_path)
        #TODO: Verify handler_options in system.yml to make sure invalid handler options and options
        # which shouldn't be overridden are not processed (ie, throw exception or something).
        handler_options = dict()
        handler_options.update(base_config['log_handlers'][handler_class_path])
        handler_options.update(system_config.get('logger_parameters', {}))

        handler_obj = handler_class(**handler_options)
        handler_obj.setLevel(message_level)
        handler_obj.setFormatter(logging.Formatter(base_config['message_format']))

        logger.addHandler(handler_obj)

    return logger

class SystemOptions(object):
    '''
    Contains system properties.
    '''
    def __init__(self, **kwargs):
        '''
        kwargs contain the system properties and their values.  We store those into separate fields.
        '''
        self._node_name = kwargs.get('node_name')
        self._logger = kwargs.get('logger')

    @property
    def node_name(self):
        '''
        Returns the name of this node.
        '''
        return self._node_name

    @property
    def logger(self):
        '''
        Returns a reference to the main logger.
        '''
        return self._logger
