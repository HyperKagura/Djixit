#Project Setup

Apart from django you will need to install some python packages. Run:

```shell script
pip install channels channels_redis
```

to use django channels with redis locally run

```shell script
 docker run -p 6379:6379 -d redis:5  
```

You might encounter the following problem:

```diff
- docker: Cannot connect to the Docker daemon at unix:///var/run/docker.sock.
```

You have two options to deal with it: (see this [stackowerflow post](https://stackoverflow.com/questions/44084846/cannot-connect-to-the-docker-daemon-on-macos))
1. Install Docker App and launch it as a usual macOS Application.
```
brew cask install docker
```
2. Install more docker-things and use it via VirtualBox macOS Application.
```
brew install docker-machine
brew install docker-compose
brew cask install virtualbox
docker-machine create --driver virtualbox default
eval "$(docker-machine env default)"
```

Now it should work.
