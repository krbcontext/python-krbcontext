
package_name=$(python3 -c "
from configparser import ConfigParser
cfg = ConfigParser()
cfg.read('setup.cfg')
print(cfg.get('package', 'name'))
")

package_rel_ver=$(python3 -c "
from configparser import ConfigParser
cfg = ConfigParser()
cfg.read('setup.cfg')
print(float(cfg.get('package', 'version')) + 0.1)
")
