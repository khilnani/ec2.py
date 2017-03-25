init:
		pip install -r requirements.txt
		pip install -e . --upgrade

clean:
		find . -name "*.pyc" -exec rm -rf {} \;
		rm -rf ec2.py.egg-info/
		rm -rf build/
		rm -rf dist/
		rm -rf test/

package:
		python setup.py sdist
		python setup.py bdist_wheel

publish:
		python setup.py register
		twine upload dist/*
