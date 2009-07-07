from os import environ

from api import Api

_api = Api(environ['LINODE_API_KEY'], debug=True)

def bool(value):
  if value in (1, '1'):
    return True
  else:
    return False

def unbool(value):
  if value:
    return 1
  else:
    return 0

class LinodeObject(object):
  fields = None
  update_method = None
  create_method = None
  primary_key   = None
  list_method   = None

  def __init__(self, entry={}):
    self.__entry = dict([(str(k).lower(),v) for k,v in entry.items()])

  def __getattr__(self, name):
    name = name.replace('_LinodeObject', '')
    if name == '__entry':
      return self.__dict__[name]
    elif not self.fields.has_key(name):
      raise AttributeError
    else:
      field, conversion, deconvert = self.fields[name]
      value = None
      if self.__entry.has_key(field.lower()):
        value = self.__entry[field.lower()]
        if conversion:
          value = conversion(value)
      return value

  def __setattr__(self, name, value):
    name = name.replace('_LinodeObject', '')
    if name == '__entry':
      object.__setattr__(self, name, value)
    elif not self.fields.has_key(name):
      raise AttributeError
    else:
      field, conversion, deconvert = self.fields[name]
      if deconvert:
        value = deconvert(value)
      elif conversion:
        value = conversion(value)
      self.__entry[field.lower()] = value

  def save(self):
    if self.id:
      self.update()
    else:
      self.id = self.create_method(**self.__entry)[self.primary_key]

  def update(self):
    self.update_method(**self.__entry)

  @classmethod
  def list(self, **kw):
    kwargs = {}
    for k, v in kw.items():
      f, c, d = self.fields[k.lower()]
      kwargs[f] = v
    for l in self.list_method(**kwargs):
      yield self(l)

  @classmethod
  def get(self, **kw):
    kwargs = {}
    for k, v in kw.items():
      f, c, d = self.fields[k.lower()]
      kwargs[f] = v
    return self(self.list_method(**kwargs)[0])

class Linode(LinodeObject):
  fields = {
    'id'                : ('LinodeID', int, None),
    'name'              : ('Label', str, None),
    'label'             : ('Label', str, None),
    'group'             : ('lpm_displayGroup', None, None),
    'cpu_enabled'       : ('Alert_cpu_enabled', bool, unbool),
    'cpu_threshold'     : ('Alert_cpu_threshold', int, None),
    'diskio_enabled'    : ('Alert_diskio_enabled', bool, unbool),
    'diskio_threshold'  : ('Alert_diskio_enabled', int, None),
    'bwin_enabled'      : ('Alert_bwin_enabled', bool, unbool),
    'bwin_threshold'    : ('Alert_bwin_threshold', int, None),
    'bwout_enabled'     : ('Alert_bwout_enabeld', bool, unbool),
    'bwout_threshold'   : ('Alert_bwout_threshold', int, None),
    'bwquota_enabled'   : ('Alert_bwquota_enabled', bool, unbool),
    'bwquota_threshold' : ('Alert_bwquota_threshold', int, None),
    'backup_window'     : ('backupWindow', None, None),
    'backup_weekly_day' : ('backupWeeklyDay', None, None),
    'watchdog'          : ('watchdog', bool, unbool),
  }

  update_method = _api.linode_update
  create_method = _api.linode_create
  primary_key   = 'LinodeID'
  list_method   = _api.linode_list

  def boot(self):
    _api.linode_boot(linodeid=self.id)

  def shutdown(self):
    _api.linode_shutdown(linodeid=self.id)

  def reboot(self):
    _api.linode_reboot(linodeid=self.id)

  def delete(self):
    _api.linode_delete(linodeid=self.id)

class LinodeDisk(LinodeObject):
  fields = {
    'id'      : ('DiskID', int, None),
    'linode'  : ('LinodeID', int, None),
    'type'    : ('Type', int, None),
    'name'    : ('Label', str, None),
    'label'   : ('Label', str, None),
  }

  update_method = _api.linode_disk_update
  create_method = _api.linode_disk_create
  primary_key   = 'DiskID'
  list_method   = _api.linode_disk_list

  def duplicate(self):
    ret = _api.linode_disk_duplicate(linodeid=self.linode, diskid=self.id)
    return LinodeDisk(LinodeDisk.get(linode=self.linode, id=ret['DiskID']))

  def resize(self, size):
    _api.linode_disk_resize(linodeid=self.linode, diskid=self.id, size=size)

  def delete(self):
    _api.linode_disk_delete(linodeid=self.linode, diskid=self.id)

class LinodeConfig(LinodeObject):
  fields = {
    'id'                  : ('ConfigID', int, None),
    'linode'              : ('LinodeID', int, None),
    'kernel'              : ('KernelID', int, None),
    'name'                : ('Label', str, None),
    'label'               : ('Label', str, None),
    'comments'            : ('Comments', str, None),
    'ram_limit'           : ('RAMLimit', int, None),
    'root_device_num'     : ('RootDeviceNum', int, None),
    'root_device_custom'  : ('RootDeviceCustom', int, None),
    'root_device_readonly': ('RootDeviceRO', bool, unbool),
    'disable_updatedb'    : ('helper_disableUpdateDB', bool, unbool),
    'helper_xen'          : ('helper_xen', bool, unbool),
    'helper_depmod'       : ('helper_depmod', bool, unbool),
  }

  update_method = _api.linode_config_update
  create_method = _api.linode_config_create
  primary_key   = 'ConfigID'
  list_method   = _api.linode_config_list

class Kernel(LinodeObject):
  fields = {
    'id'    : ('KernelID', int, None),
    'label' : ('Label', str, None),
    'name'  : ('Label', str, None),
    'is_xen': ('IsXen', bool, unbool),
  }

  list_method = _api.avail_kernels

class Distribution(LinodeObject):
  fields = {
    'id'        : ('DistributionID', int, None),
    'label'     : ('Label', str, None),
    'name'      : ('Label', str, None),
    'min'       : ('MinImageSize', int, None),
    'is_64bit'  : ('Is64Bit', bool, unbool),
    'created'   : ('CREATE_DT', None, None),
  }

  list_method = _api.avail_distributions

class Datacenter(LinodeObject):
  fields = {
    'id'        : ('DatacenterID', int, None),
    'location'  : ('Location', str, None),
    'name'      : ('Location', str, None),
  }

  list_method = _api.avail_datacenters
