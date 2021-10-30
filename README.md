# mciwb
Minecraft Interactive world builder

Additional functions on top of the mcwb world builder library to allow
interactive world building using ipython and a minecraft client in tandem.

## Intro
The interaction is achieved by dropping command signs into the world.
You can also switch back to the iPython console and execute commands.

To initiate an interacive session create a Copy object and
pass the player's name. See demo.py for example usage.

The player will be given one of each of the command signs
currently available. The player can then invoke these
commands and indicate a block location by placing one of
these signs in game.

See the following video for a quick sample of the capabilities:

https://user-images.githubusercontent.com/964827/139144276-8c14ddc4-350f-4e7f-b393-2ec4187c5870.mp4

## Interactive Commands
So far we have the following signs to drop. See demo.py for example usage.
(video shows start and stop signs which are now combined into
the single command 'select')

When you drop a sign you must be facing it. It will disappear when
the sign has been detected by the poller and the function has executed.

Note that the sign's target coordinates are the block **behind** it and
a free standing sign targets the block below it.

- **select**: set the start and stop point for the copy buffer, the last two
uses of this command determine the bounding box of the copy buffer. The last
use determines the anchor point for the next paste
- **expand**: expand the closest face of the copy buffer to the indicated point (can do all 6 faces)
- **paste**: clone the contents of copy buffer to the current
indicated location (anchored at most recent 'select' point)
- **clear**: clear the contents of the paste buffer
- **backup** create a zipped and dated backup of the world

## Todo Interactive Commands

- **shift**: shift the copy buffer until the closest face is at the indicated point

## Useful iPython Commands

Using iPython you can also interact with the same Copy object
your player is using in the game.

The following useful commands are available on the Copy class:

- **shift**: shift the copy buffer in any dimension
- **expand**: expand the copy buffer by moving one of its faces
outwards
- **paste**: paste at the paste location with offset. Can
be used in a loop to make repeating structures.
- **restore**: restore the world to a previous backup

## Todo iPython Commands

- These planned commands take advantage of exisiting functions in mcwb library.

  - **save**: save the copy buffer to a named file
  - **load**: load a file into the world at the copy buffer start point. Set the copy buffer to enclose the loaded structure
  - **rotate**: perform transforms on the copy buffer
- These require additional support in mcwb required (profile generators)

  - **rectangle**: make a rectangle described by copy buffer
  corners (expects one of the copy dimensions to be size 1)
  - **elipse**: make a elipse described by copy buffer
  corners (expects one of the copy dimensions to be size 1)
