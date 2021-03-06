import redgreenunittest as unittest
from glob import glob


testmodules = []
for f in glob('test_*.py'):
    testmodules.append(f.replace('.py',''))

#print testmodules


'''
testmodules = [
    'test_ss',
    'test_auth',
    'test_login',
    'test_user_online',
    'test_contact_list',
    'test_url_by_name',
    'test_profile_user',
    'test_get_room'
    ]
'''

suite = unittest.TestSuite()

for t in testmodules:
    try:
        # If the module defines a suite() function, call it to get the suite.
        mod = __import__(t, globals(), locals(), ['suite'])
        suitefn = getattr(mod, 'suite')
        suite.addTest(suitefn())
    except (ImportError, AttributeError):
        # else, just load all the test cases from the module.
        suite.addTest(unittest.defaultTestLoader.loadTestsFromName(t))

unittest.TextTestRunner(verbosity=2).run(suite)
