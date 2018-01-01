Integrates [GMod], primarily [TTT], with Mumble via [Mumo].

This module automatically moves Mumble users between different channels based on whether they are alive or dead in GMod.
A companion GMod addon is required on the server to provide this functionallity.
Intended to be used with [a custom Murmur server](https://github.com/johni0702/mumble/tree/secret-channels) which allows dead players to appear as if they are in the same channel as alive ones while in fact they are not.

This module does not affect users outside of its three controlled channels (one lobby, one for people still alive and one for dead people).
Users in the lobby channel are automatically moved to the dead/alive channels if they are ingame and back if they disconnect from the game.
Users in either the dead or the alive channel are automatically moved depending on their state in the game. *If a user dies in the game, they will be moved to the dead channel but will appear to remain in the alive channel for all remaining players.*

### Installation
#### Mumble
For the module to work properly you have to create at least three channels.
Note that the bot adds dead players to a group named "dead" in the lobby channel which can be used to prevent dead players from speaking to lobby/alive players.
The recommended setup is having a "GMod" channel which has two sub channels, one "Alive" and one "Dead" (names can be chosen freely), along with the folling ACL entries:
- On "GMod": @dead -speak (applies to this+sub)
- On "Alive" and "Dead": @all -enter
- On "Dead": @dead +speak
Then add an empty group named "members hidden" to the "Dead" channel and link it to the "Alive" channel to activate the secret-channels feature of the custom Murmur version.
If you want to allow spectators / unregistered users to talk to alive players and be heared by dead players, link "Alive" to "GMod".

#### Mumo
To install the Mumo module, copy `mumo/gmod.py` into the `modules` folder of your Mumo installation, copy `mumo/gmod.ini` into the `modules-available` folder of your Mumo installation and create a symlink to it in the `modules-enabled` folder to enable it: `ln -s modules-available/gmod.ini modules-enabled/`

Before restarting Mumo, make sure to configure the module in the `gmod.ini` file.

#### GMod
To install the companion GMod addon, copy the `gmod/mumble` folder into the `garrysmod/addons` folder of your GMod installation.

Next create a plain text file at `garrysmod/data/mumble.config.txt` whose only content is the URL to the mumo module configured above.
If your GMod server and Mumo are running on the same machine, the URL will be `http://localhost:8088/YourSecretHere/`.

[GMod]: https://gmod.facepunch.com/
[TTT]: http://ttt.badking.net/
[Mumo]: https://wiki.mumble.info/wiki/Mumo
