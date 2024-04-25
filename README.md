**TAMV _is under active development!_**
# Table of Contents
- [TAMV Walkthrough Video](#tamv-in-action)
- [TAMV = Tool Alignment (using) Machine Vision](#tamv--tool-alignment-using-machine-vision)
- [Why should I use this version/fork of TAMV?](#why-should-i-use-this-versionfork-of-tamv)
- [What do I need to run TAMV?](#what-do-i-need-to-run-tamv)
- [TAMV Community Videos](#tamv-community-videos)

**You can find me (H2B) on the [Jubilee Discord Server](https://discord.gg/XkphRqb) and I'll be more than glad to help you get things up and running.**

# TAMV in Action
We've got a short walkthrough of TAMV in operation up on YouTube, and there you can see a real-time setup and alignment for a 3 tool printer. Click on the image to head over there!
<p align="center">
<a href="https://youtu.be/1nGc_hFzK0s?t=5"><img src="resources/video_cap.png">
</p>

_[back to top](#table-of-contents)_
# TAMV = Tool Alignment (using) Machine Vision
Ever needed to simplify nozzle and tool alignment on a toolchanging 3D printer/machine? 

Well, welcome to the wonderful experience of **automated nozzle alignment** and Z offset setting using machine vision (for X&Y offset alignment) and electrical touch plates (for Z offset alignment).

This program significantly improves how tool-changing machines using Duet RRF v2/3 on Duet2 / Duet3 controlers by leveraging open-source computer vision algorithms from the OpenCV project to eliminate the guesswork from tool alignment and (nearly) completely automate the process. Let the machines do the work!

TAMV in its current release is a graphical program that allows you to connect to your printer and automatically calculate tool offsets in XY space using a generic [USB microscope](https://www.amazon.com/dp/B06WD843ZM) and a Raspberry Pi (preferably a Pi4 or better with 4GB of RAM). You may also use any Windows or Linux desktop/laptop, as long as you can connect that machine to the microscope situated on the printer build plate. 

Please avoid using any webcams for alignment, because this approach (while viable) will need significantly more work to overcome issues related to insufficient/inappropriate lighting and limited depth-of-field of webcam optics (not to mention more sensor noise artifacts), all of which can throw off the computer vision algorithms and cause headaches.

_[back to top](#table-of-contents)_
# Why should I use this version/fork of TAMV?
1. Its got a bundled installation script for getting OpenCV 4.5.1 running on a Raspberry Pi.
2. **It takes about 5 minutes to install.**
3. TAMV is fully multi-processing and multi-threading for faster run times.
4. Automatically calibrates itself for optical distortions, making alignment smoother and faster.
5. Switches automatically between 4 different detection modes to lock on to the nozzle quickly.
6. Fails over to manual alignment capture when the nozzle can't be detected.
7. **Supports manual or semi-assisted alignments so you can use it with any tools in your toolchanger**
7. Its built to be extensible, and we do have a few klipper beta testers working on a driver for klipper toolchangers!
8. You can save multiple printer profiles and re-use your connections every time you align your tools.
9. **Its completely open-source and community driven.**

_[back to top](#table-of-contents)_
# What do I need to run TAMV?
Please visit [the TAMV page on the Jubilee Wiki](https://jubilee3d.com/index.php?title=TAMV) for isntallation instructions.


_[back to top](#table-of-contents)_
# TAMV Community Videos
## Danal's Original TAMV Release
You can find the original release of [TAMV in Danal Estes' repository](https://github.com/DanalEstes/TAMV).

[![Danal's Original TAMV Release](http://img.youtube.com/vi/e_d_XHwGfRM/0.jpg)](https://www.youtube.com/watch?v=e_d_XHwGfRM)
## Walkthrough: Luke's Laboratory
Be sure to check out [Luke's latest releases on his website](https://www.lukeslab.online/).

[![Luke's Laboratory Walkthrough](http://img.youtube.com/vi/ZjgjIAw_s7E/0.jpg)](https://www.youtube.com/watch?v=ZjgjIAw_s7E)
## Walkthrough: Reefing Ninja
[![Reefing Ninja's Walkthrough](http://img.youtube.com/vi/uPa1ecRxpr4/0.jpg)](https://www.youtube.com/watch?v=uPa1ecRxpr4)

_[back to top](#table-of-contents)_
