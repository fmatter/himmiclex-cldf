from setuptools import setup


setup(
    name='cldfbench_himmiclex-cldf',
    py_modules=['cldfbench_himmiclex-cldf'],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'cldfbench.dataset': [
            'himmiclex-cldf=cldfbench_himmiclex-cldf:Dataset',
        ]
    },
    install_requires=[
        'cldfbench',
    ],
    extras_require={
        'test': [
            'pytest-cldf',
        ],
    },
)