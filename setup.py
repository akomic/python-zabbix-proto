from distutils.core import setup

setup(name='ZabbixProto',
      version='0.0.9',
      description='Zabbix Communication Protocols',
      author='Alen Komic',
      author_email='akomic@gmail.com',
      url='https://github.com/akomic/python-zabbix-proto',
      download_url='https://github.com/akomic/python-zabbix-proto/archive/v0.0.9.tar.gz',
      packages=['zabbixproto'],
      install_requires=[
          'datetime'
      ],
      keywords='Zabbix Protocols Sender Proxy Agent',
      license='Apache Software License',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: Apache Software License',
          'Programming Language :: Python :: 3',
          'Topic :: System :: Monitoring',
          'Topic :: System :: Networking :: Monitoring',
          'Topic :: System :: Systems Administration'
      ]
      )
