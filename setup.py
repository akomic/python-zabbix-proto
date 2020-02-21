from distutils.core import setup

setup(name='ZabbixProto',
      version='0.0.1',
      description='Zabbix Communication Protocols',
      long_description=open('README.rst', 'r').read() + '\n\n' + open(
          'CHANGELOG.rst', 'r').read(),
      author='Alen Komic',
      author_email='akomic@gmail.com',
      url='https://github.com/akomic/python-zabbix-proto',
      download_url='https://github.com/akomic/python-zabbix-proto/archive/0.0.1.tar.gz',
      packages=['zabbixproto'],
      install_requires=[
          'datetime',
          'json',
          're',
          'socket',
          'struct',
          'time'
      ],
      keywords='Zabbix Protocols Sender Proxy Agent',
      license='Apache Software License',
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'License :: OSI Approved :: Apache Software License',
          'Programming Language :: Python :: 3',
          'Topic :: System :: Monitoring',
          'Topic :: System :: Networking :: Monitoring',
          'Topic :: System :: Systems Administration'
      ]
      )
