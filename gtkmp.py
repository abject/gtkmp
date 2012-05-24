#!/usr/bin/env python
#-*-coding: utf8 -*-

"""
	Copyright 2012, abject, abject[at]live[dot].fr

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import pygtk
pygtk.require('2.0')
import gtk
import os
import time

## Path to FIFO file
PIPE_PATH = '/tmp/mplayer'

class Player(gtk.Socket):
    """ Interface between mplayer and main script

    gtk.Socket -> Target Frame for external program
    """

    def __init__(self, id):
        """ Initialize Player class
        Need an id to create a pipe between mplayer and the GUI
        """
        ## Init gtk.Socket instance
        gtk.Socket.__init__(self)

        # Create FIFO file for pipe connection
        self.pipe = PIPE_PATH + str(id)
        ## Remove pipe file with same name if exist
        ##TODO: Find a strong FIFO file test in python to remove file if exist
        try:
            os.unlink(self.pipe)
        except:
            pass
        ## Create pipe file
        os.mkfifo(self.pipe)
        os.chmod(self.pipe, 0666)

        ## Player.start serve to control if mplayer is launched or not
        self.start = False

    def cmdplayer(self, cmd):
        """ Exec cmd in mplayer
        Write cmd+'\n' in pipe file to be execute by mplayer
        """
        open(self.pipe, 'w').write(cmd+'\n')

    def setwid(self, wid):
        """ Run mplayer in slave mode with input piped to self.pipe file

        For other mplayer options, See man mplayer
        """
        ## Run mplayer in slave mode
        os.system("mplayer -nojoystick -nolirc -slave -vo x11 -wid %s -vf scale=400:200 -idle -input file=%s &"%(wid, self.pipe))
        ## Declare mplayer as running
        self.start = True

    def loadfile(self, filename):
        """ Load a file with mplayer
        """
        ## TODO: Create Error Statement to raise properly this error
        if not self.start:
            print "You nedd to set wid to mplayer.... see Player.setwid(wid)"
            raise
        else:
            self.cmdplayer("loadfile %s"%(filename))
            self.cmdplayer("change_resctangle w=100:h=100")

    ## TODO: There is no button for pause in PlayerFrame. Add it !
    def pause(self, parent):
        """ Send 'pause' command to mplayer
        """
        self.cmdplayer("pause")

    def forward(self, parent):
        """ Send 'seek +10 0' command to mplayer
        """
        self.cmdplayer("seek +10 0")

    def backward(self, parent):
        """ Send 'seek -10 0' command to mplayer
        """
        self.cmdplayer("seek -10 0")

    def quit(self):
        """ Send 'quit' command to mplayer
        """
        self.cmdplayer("quit")
        self.start = False

class PlayerFrame(gtk.Table):
    """ Frame within the movie output, button control and so
    """

    def __init__(self, root, id):
        """ Init class

        root: Main Window (needed to quit the GUI properly with Root.quit function)
        id: Integer need to pipe mplayer and Player class
        """
        self.root = root
        gtk.Table.__init__(self, rows=2, columns=4)
        self.set_col_spacings(10)
        self.set_row_spacings(10)

        # Load Player
        self.Screen = Player(id)
        self.Screen.set_size_request(100, 100)
        self.attach(self.Screen, 0, 5, 0, 1, xoptions=gtk.EXPAND|gtk.FILL|gtk.SHRINK, yoptions=gtk.EXPAND|gtk.FILL|gtk.SHRINK, xpadding=5, ypadding=5)

        # Open
        BttOpen = gtk.Button(stock=("gtk-open"))
        BttOpen.connect("clicked", self.open)
        self.attach(BttOpen, 0, 1, 1, 2)

        # Forward
        BttFw = gtk.Button(label="Forward")
        BttFw.connect("clicked", self.Screen.forward)
        self.attach(BttFw, 2, 3, 1, 2)

        # Backward
        BttBw = gtk.Button(label="Backward")
        BttBw.connect("clicked", self.Screen.backward)
        self.attach(BttBw, 1, 2, 1, 2)

        # Quit
        Bttquit = gtk.Button(stock=('gtk-quit'))
        Bttquit.connect("clicked", lambda w: self.quit(self.root))
        self.attach(Bttquit, 3, 4, 1, 2)

    def quit(self, root):
        """ Quit using root.quit function
        """
        root.quit()

    def open(self, parent):
        """ Open file thanks to a dialog GUI
        """
        dialog = gtk.FileChooserDialog("Select File", gtk.Window(), gtk.FILE_CHOOSER_ACTION_OPEN,
                                       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.connect("destroy", lambda w: dialog.destroy())
        statut = dialog.run()
        if statut == gtk.RESPONSE_OK:
            self.Screen.loadfile(dialog.get_filename().replace(' ', '\ '))
        dialog.destroy()

class Root:
    """ Root windows containing all the subframe
    """

    def __init__(self):
        ## Create the main Window
        root = gtk.Window()
        root.set_title("Movie player")
        root.set_default_size(500, 400)
        root.set_position(gtk.WIN_POS_CENTER)
        root.connect("destroy", self.quit)

        ## Load PlayerFrame and add it to root
        self.screen = PlayerFrame(self, 1)
        root.add(self.screen)

        ## Show all
        root.show_all()

        ## Send frame id to mplayer after showing it
        self.screen.Screen.setwid(long(self.screen.Screen.get_id()))

    def quit(self, *parent):
        """ Properly function quit by killing the mplayer process before quitting the GUI
        """
        ## Send signal to quit mplayer properly
        self.screen.Screen.quit()
        ## Wait mplayer is closed
        time.sleep(0.1)
        ## Quit main GUI
        gtk.main_quit()

    def loop(self):
        """ Main loop event
        """
        gtk.main()
        

r = Root()
r.loop()
