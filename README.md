# fo_training

## Getting started

* Install prerequisits
* make sure to have a running instance of https://gitlab.uni-bayreuth.de:dmkg/fluon-refsrv running
* configure URL of instance in Makefile and adjust credentials of user in `Makefile.local`:
  ```
  PUB_DEST:=/some/personal/copy/of/the/folder
  PUB_ENDPOINT_PASSWD:=fluon-account-password-goes-here
  ```

* ```make publish```
* fix bugs :)
