import fcntl


class ToolLock(object):
  def __init__(self, name):
    self.handle = open(name, 'w')

  def lock(self):
    fcntl.flock(self.handle, fcntl.LOCK_EX)

  def unlock(self):
    fcntl.flock(self.handle, fcntl.LOCK_UN)

  def __del__(self):
    try:
      self.handle.close()
    except:
      pass