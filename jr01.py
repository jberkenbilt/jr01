#!/usr/bin/env python
# -*-python-*-
#
# $Id: jr01.py,v 1.1 1999-07-10 16:08:08 ejb Exp $
# $Source: /work/cvs/jr01/jr01.py,v $
# $Author: ejb $
#

import Tkinter;

class JR01State:
    nbars = 3
    npegs = 7
    pass

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
    vline_overhang = 20
    peg_gap = 60
    first_peg = peg_gap + bar_hmargin
    bar_delta = 12
    bar_sensitivity = 5 # snap to position when within bar_sensitivity pixels
    bottom_height = 135 # XXX
    peg_outer_radius = 8
    peg_inner_radius = 3

    # Computed Geometry
    bar_width = (JR01State.npegs + 1) * peg_gap
    width = bar_width + 2 * bar_hmargin
    bar_left = bar_hmargin
    bar_right = bar_hmargin + bar_width
    first_bar_top = bar_vmargin

    vline_top = bar_vmargin - vline_overhang
    vline_height = (bar_gap * (JR01State.nbars - 1) + bar_height +
                    2 * vline_overhang)

    bar_area_height = ((2 * bar_vmargin) +
                       ((JR01State.nbars - 1) * bar_gap) +
                       bar_height)
    height = bar_area_height + bottom_height
    peg_vcenter_offset = (bar_height / 2)
    peg_inner_top_offset = (bar_height / 2)

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

    # Pegstates maps a peg item to its corresponding Pegstate object
    pegtag = "peg"
    pegstates = {}

    class Pegstate:
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

            

    def __init__(self, tk, state):
        frame = Tkinter.Frame(tk, background="black",
                              highlightthickness=20,
                              highlightcolor=self.barcolor,
                              highlightbackground=self.barcolor)
        frame.pack()

        quit_button = Tkinter.Button(frame, text="quit",
                                     command=frame.quit)
        quit_button.grid(row=1, col=0)

        canvas = Tkinter.Canvas(frame, width=self.width, height=self.height,
                                background=self.bgcolor,
                                borderwidth=0, highlightthickness=0,
                                cursor="hand2")
        canvas.grid(row=0, col=0)
        
        self.draw_static_marks(canvas)

        for i in range(0, JR01State.nbars):
            self.create_bar(canvas, i, self.first_bar_top + i * self.bar_gap)

        canvas.tag_bind(self.movable, "<ButtonPress-1>", self.bar_set_cb)
        canvas.tag_bind(self.movable, "<B1-Motion>", self.bar_move_cb)
        canvas.tag_bind(self.pegtag, "<ButtonPress-1>", self.toggle_peg)

    def draw_static_marks(self, canvas):
        for i in range(0, JR01State.npegs):
            x = self.first_peg + i * self.peg_gap
            canvas.create_line(x, self.vline_top,
                               x, self.vline_top + self.vline_height,
                               fill=self.markcolor)


    def create_bar(self, canvas, barnum, top):
        grouptag = "bar-" + `barnum`
        main_item = canvas.create_rectangle(self.bar_left,
                                            top,
                                            self.bar_right,
                                            self.bar_height + top,
                                            tags = (grouptag, self.movable),
                                            width = 2,
                                            fill = self.barcolor)
        self.move_sets[main_item] = (main_item, grouptag)
        item = canvas.create_rectangle(self.bar_right - 15,
                                       top + 2,
                                       self.bar_right - 4,
                                       top + self.bar_height - 4,
                                       tags = (grouptag, self.movable),
                                       width = 0, fill=self.barshadow)
        self.move_sets[item] = (main_item, grouptag)

        for i in range(0, JR01State.npegs):
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

            pegstate = self.Pegstate(state, barnum, pegnum, dx, canvas,
                                     outer_item, inner_item)
            self.pegstates[outer_item] = pegstate
            self.pegstates[inner_item] = pegstate

#        self.sets[item] = "set-2"
#        item = canvas.create_oval(170, 260, 230, 320,
#                                  tags=("set-2", "toggleable"))
#        self.toggle_states[item] = [1, "#0a0", "#060"];
#        item = canvas.create_oval(190, 280, 210, 300,
#                                  tags="set-2", fill="black")
#
#        canvas.tag_bind("toggleable", "<Button-1>", self.toggle_state)
#
#        for item in canvas.find_withtag("toggleable"):
#            data = self.toggle_states[item]
#            index = data[0]
#            canvas.itemconfigure(item, fill=data[index])

    def toggle_peg(self, event):
        canvas = event.widget
        item = canvas.find_withtag(Tkinter.CURRENT)[0]
        if self.pegstates.has_key(item):
            pegstate = self.pegstates[item]
            pegstate.toggle()

    def bar_set_cb(self, event):
        self.last_x = event.x

    def bar_move_cb(self, event):
        canvas = event.widget
        item = canvas.find_withtag(Tkinter.CURRENT)[0]

        items = (item,)
        coords = canvas.coords(item)

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


        for item in items:
            canvas.move(item, dx, 0)

        self.last_x = self.last_x + dx

root = Tkinter.Tk()
root.title("JR01")
root.resizable(0, 0)
state = JR01State()
JR01Win(root, state)
try:
    root.mainloop()
except KeyboardInterrupt:
    pass

