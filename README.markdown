ABOUT THIS PROJECT
------------------
The xmlrpc interface to rTorrent is extremely unintuitive and has very little documentation, this project aims to make interfacing with rTorrent much easier.

ABOUT 1.0
-----------
After years of stagnation, I've decided to do a full rewrite of this project.
I wasn't happy with the user facing API, and value caching was essentially broken.

My primary goals for this release:
  - An API for any user
    - Simple APIs for scripting
    - Flexible APIs for fine-grained calls
  - Separation of live and cached data:
    - Previously, any call that returned data stored that data as an instance variable
      within the object. This feature was essentially broken and will be
      replaced with a better solution.
  - Cleaner code
  - Better documentation
  
CONTRIBUTIONS
-------------
I don't expect to release the final version of 1.0 for awhile, and
I'm welcome to suggestions during this alpha period. If there is
anything that frustrated you previously or improvements you wish could be added,
feel free to create an issue for it.