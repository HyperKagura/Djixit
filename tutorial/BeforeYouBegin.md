# Before You Begin

##Installing Homebrew, pyenv and python.

Get Homebrew if you haven't already, configure your favorite venv and install python. I am using python 3.7.5 with pyenv.
I used this [guide](https://medium.com/python-every-day/python-development-on-macos-with-pyenv-2509c694a808) 

I copy the guide below

Install [Homebrew](https://brew.sh/) if it isn't already available
```
/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)" 
```

Install pyenv

```shell script
brew install pyenv 
```

Add pyenv initializer to shell startup script
```shell script
echo 'eval "$(pyenv init -)"' >> ~/.zshrc 
```

Reload your profile
```shell script
source ~/.zshrc
```

### Pyenv Usage Guide

#### Install python version

Now when `pyenv` is installed and functioning we can install multiple versions of Python and switch between them easily.
View available python versions with
```shell script
pyenv install --list.
```

select version you like and install it with
```shell script
pyenv install <python-version>
```
for instance:
```shell script
pyenv install 3.7.2
```

Now that we’ve installed Python 3.7.2 let’s take a look at all the installed versions available on our system:
```shell script
pyenv versions
```

You should see system and 3.7.2.

#### Set Global Python
```shell script
pyenv global 3.7.2
```

Now whenever you call python you’ll be using Python 3.7.2. Check it with 
```shell script
python --version.
```

#### Set Local Python

To set a Python version for a specific project, cd into your project and then run:

```shell script
pyenv local <python-version>
```

That will create a .python-version file in the current directory which pyenv will see and use to set the appropriate version.

Small advice for beginners: my favorite python IDE is PyCharm. Check this out if you don't have preferences yet.