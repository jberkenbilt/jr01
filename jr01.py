#!/usr/bin/env python
# -*-python-*-
#
# $Id: jr01.py,v 1.2 1999-07-10 16:47:17 ejb Exp $
# $Source: /work/cvs/jr01/jr01.py,v $
# $Author: ejb $
#

import Tkinter;

class JR01State:
    def __init__(self, bars = 3, pegs = 7):
        self.nbars = bars
        self.npegs = pegs

    def set_peg_state(self, barnum, pegnum, position, state):
        print "set peg", (barnum, pegnum, position), "to state", state

    def set_bar_position(self, barnum, position):
        print "set bar", barnum, "to position", position


class JR01Win:
    # Appearance
    barcolor = "#2d4245"
    barshadow = "#0f1c12"
    bgcolor = "#81978a"
    markcolor = "#6f6764"

    # Static Geometry
    bar_hmargin = 60
    bar_vmargin = 45
    bar_height = 35
    bar_gap = 70
    handle_width = 15
    vline_overhang = 20
    peg_gap = 60
    first_peg = peg_gap + bar_hmargin
    bar_delta = 12
    bar_sensitivity = 5 # snap to position when within bar_sensitivity pixels
    bottom_height = 135 # XXX
    peg_outer_radius = 8
    peg_inner_radius = 3

    # State information

    # Each item with the "movable" tag is expected to have an entry in
    # move_sets.  The key is the item number, and the value is a
    # 2-tuple whose first value is the "main item" in the move set and
    # whose second item is a tag that identifies all items in the move
    # set.  The main item is the item whose coordinates are used to
    # enforce any constraints that may be imposed upon moving the
    # item.  The effect is that all items in the same move_set are
    # always moved together.
    movable = "movable"
    move_sets = {}

    # "bars" maps a bar item to its corresponding Bar object
    bartag = "bar"
    bars = {}

    class Bar:
        def __init__(self, jr01_state, barnum):
            self.jr01_state = jr01_state
            self.barnum = barnum
            self.position = None

        def set_position(self, position):
            if self.position != position:
                self.position = position
                self.jr01_state.set_bar_position(self.barnum, position)

    # "pegs" maps a peg item to its corresponding Peg object
    pegtag = "peg"
    pegs = {}

    class Peg:
        def __init__(self, jr01_state, barnum, pegnum, offset, canvas,
                     outer_item, inner_item):
            self.jr01_state = jr01_state
            self.barnum = barnum
            self.pegnum = pegnum
            self.canvas = canvas
            self.outer_item = outer_item
            self.inner_item = inner_item
            self.position = (offset > 0)
            self.state = 0

        def toggle(self):
            self.state = 1 - self.state
            if self.state:
                self.canvas.itemconfigure(self.outer_item, fill="black")
                self.canvas.itemconfigure(self.inner_item, fill="black")
            else:
                self.canvas.itemconfigure(self.outer_item,
                                          fill=JR01Win.barcolor)
                self.canvas.itemconfigure(self.inner_item,
                                          fill=JR01Win.barshadow)
            self.jr01_state.set_peg_state(self.barnum, self.pegnum,
                                          self.position, self.state)
            

    def __init__(self, tk, state):
        self.state = state

        # Compute Geometry
        self.bar_width = (state.npegs + 1) * self.peg_gap
        self.bar_left = self.bar_hmargin
        self.bar_right = self.bar_hmargin + self.bar_width
        self.first_bar_top = self.bar_vmargin

        self.vline_top = self.bar_vmargin - self.vline_overhang
        self.vline_height = (self.bar_gap * (state.nbars - 1) +
                             self.bar_height +
                             2 * self.vline_overhang)

        bar_area_height = ((2 * self.bar_vmargin) +
                           ((state.nbars - 1) * self.bar_gap) +
                           self.bar_height)
        self.peg_vcenter_offset = (self.bar_height / 2)

        width = self.bar_width + 2 * self.bar_hmargin
        height = bar_area_height + self.bottom_height

        frame = Tkinter.Frame(tk, background="black",
                              highlightthickness=20,
                              highlightcolor=self.barcolor,
                              highlightbackground=self.barcolor)
        frame.pack()

        quit_button = Tkinter.Button(frame, text="quit",
                                     command=frame.quit)
        quit_button.grid(row=1, col=0)

        canvas = Tkinter.Canvas(frame, width=width, height=height,
                                background=self.bgcolor,
                                borderwidth=0, highlightthickness=0,
                                cursor="hand2")
        canvas.grid(row=0, col=0)
        
        self.draw_static_marks(canvas)

        for i in range(0, self.state.nbars):
            self.create_bar(canvas, i, self.first_bar_top + i * self.bar_gap)

        canvas.tag_bind(self.movable, "<ButtonPress-1>", self.bar_set_cb)
        canvas.tag_bind(self.movable, "<B1-Motion>", self.bar_move_cb)
        canvas.tag_bind(self.pegtag, "<ButtonPress-1>", self.toggle_peg)

    def draw_static_marks(self, canvas):
        for i in range(0, self.state.npegs):
            x = self.first_peg + i * self.peg_gap
            canvas.create_line(x, self.vline_top,
                               x, self.vline_top + self.vline_height,
                               fill=self.markcolor)


    def create_bar(self, canvas, barnum, top):
        grouptag = self.bartag + "-" + `barnum`
        main_item = canvas.create_rectangle(self.bar_left,
                                            top,
                                            self.bar_right,
                                            self.bar_height + top,
                                            tags = (grouptag, self.movable),
                                            width = 2,
                                            fill = self.barcolor)
        self.move_sets[main_item] = (main_item, grouptag)
        handle = canvas.create_rectangle(self.bar_right - self.handle_width,
                                       top + 2,
                                       self.bar_right - 4,
                                       top + self.bar_height - 4,
                                       tags = (grouptag, self.movable),
                                       width = 0, fill=self.barshadow)
        self.move_sets[handle] = (main_item, grouptag)

        bar = self.Bar(self.state, barnum)
        self.bars[main_item] = bar
        self.bars[handle] = bar

        for i in range(0, self.state.npegs):
            self.create_peg(canvas, grouptag, top, main_item, barnum, i)

    def create_peg(self, canvas, grouptag, top, main_item, barnum, pegnum):

        for dx in (-self.bar_delta, self.bar_delta):

            peg_x = self.first_peg + pegnum * self.peg_gap
            peg_y = top + self.peg_vcenter_offset

            outer_item = canvas.create_oval(
                dx + peg_x - self.peg_outer_radius,
                peg_y - self.peg_outer_radius,
                dx + peg_x + self.peg_outer_radius,
                peg_y + self.peg_outer_radius,
                tags = (grouptag, self.pegtag),
                outline = "",
                fill=self.barcolor)
            
            inner_item = canvas.create_oval(
                dx + peg_x - self.peg_inner_radius,
                peg_y - self.peg_inner_radius,
                dx + peg_x + self.peg_inner_radius,
                peg_y + self.peg_inner_radius,
                tags = (grouptag, self.pegtag),
                fill=self.barshadow)

            peg = self.Peg(self.state, barnum, pegnum, dx, canvas,
                           outer_item, inner_item)
            self.pegs[outer_item] = peg
            self.pegs[inner_item] = peg

    def toggle_peg(self, event):
        canvas = event.widget
        item = canvas.find_withtag(Tkinter.CURRENT)[0]
        if self.pegs.has_key(item):
            peg = self.pegs[item]
            peg.toggle()

    def bar_set_cb(self, event):
        self.last_x = event.x

    def bar_move_cb(self, event):
        canvas = event.widget
        item = canvas.find_withtag(Tkinter.CURRENT)[0]

        items = (item,)
        coords = canvas.coords(item)

        bar = None
        if (self.bars.has_key(item)):
            bar = self.bars[item]

        if self.move_sets.has_key(item):
            coords = canvas.coords(self.move_sets[item][0])
            items = canvas.find_withtag(self.move_sets[item][1])

        minleft = self.bar_left - self.bar_delta
        maxleft = self.bar_left + self.bar_delta

        dx = event.x - self.last_x

        newleft = coords[0] + dx

        if newleft < minleft + self.bar_sensitivity:
            dx = minleft - coords[0]
        elif newleft > maxleft - self.bar_sensitivity:
            dx = maxleft - coords[0]
        elif (self.bar_left - self.bar_sensitivity <
              newleft <
              self.bar_left + self.bar_sensitivity):
            dx = self.bar_left - coords[0]

        newleft = coords[0] + dx

        if bar:
            if newleft == minleft:
                bar.set_position(0)
            elif newleft == maxleft:
                bar.set_position(1)
            else:
                bar.set_position(None)

        for item in items:
            canvas.move(item, dx, 0)

        self.last_x = self.last_x + dx

root = Tkinter.Tk()
root.title("JR01")
root.resizable(0, 0)
JR01Win(root, JR01State(3, 7))
try:
    root.mainloop()
except KeyboardInterrupt:
    pass

