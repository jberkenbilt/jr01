#!/usr/bin/env python
# -*-python-*-
#
# $Id: jr01.py,v 1.4 1999-07-10 20:28:35 ejb Exp $
# $Source: /work/cvs/jr01/jr01.py,v $
# $Author: ejb $
#

import Tkinter;

class JR01State:
    def __init__(self, bars = 3, pegs = 7, lights = 4):
        self.nbars = bars
        self.npegs = pegs
        self.nlights = lights

    def set_peg_state(self, barnum, pegnum, position, state):
        print "set peg", (barnum, pegnum, position), "to state", state

    def set_bar_position(self, barnum, position):
        print "set bar", barnum, "to position", position

    def set_patch(self, source, dest, count):
        print "increasing connection count from column", source, "to light", dest, "by", count

class JR01Win:
    # Exceptions
    class InternalError(Exception):
        pass

    # Appearance
    background = "black"
    barcolor = "#2d4245"
    barshadow = "#0f1c12"
    bgcolor = "#81978a"
    markcolor = "#6f6764"
    ringcolor = "#ffdc95"
    redlightoff = "#4d3739"
    greenlightoff = "#324033"
    pegcolor = "black"
    ringholecolor = "black"
    linecolor = "black"
    selectedlinecolor = "blue"

    # Static Geometry
    bar_hmargin = 60
    bar_vmargin = 45
    bar_height = 35
    bar_gap = 70
    handle_width = 15
    vline_overhang = 20
    peg_gap = 60
    first_peg_x = peg_gap + bar_hmargin
    bar_delta = 12
    bar_sensitivity = 5 # snap to position when within bar_sensitivity pixels
    peg_outer_radius = 8
    peg_inner_radius = 3
    ring_gap = 10
    ring_outer_radius = 6
    ring_inner_radius = 3
    light_radius = 15
    light_top_gap = 70
    light_bottom_gap = 20
    bottom_height = light_top_gap + 2 * light_radius + light_bottom_gap
    linewidth = 6;

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
                self.canvas.itemconfigure(self.outer_item, fill=self.pegcolor)
                self.canvas.itemconfigure(self.inner_item, fill=self.pegcolor)
            else:
                self.canvas.itemconfigure(self.outer_item,
                                          fill=JR01Win.barcolor)
                self.canvas.itemconfigure(self.inner_item,
                                          fill=JR01Win.barshadow)
            self.jr01_state.set_peg_state(self.barnum, self.pegnum,
                                          self.position, self.state)
            
    # "sourcedata" and "destdata" store information for line drawing
    linetag = "line"
    cur_line = None
    sourcetag = "source"
    sourcedata = {}
    desttag = "dest"
    destdata = {}

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
        self.bar_ring_y = (self.vline_top + self.vline_height +
                                self.ring_gap)
        self.light_ring_y = self.bar_ring_y + self.light_top_gap
        self.light_y = (self.light_ring_y + self.ring_gap +
                        self.light_radius)

        bar_area_height = ((2 * self.bar_vmargin) +
                           ((state.nbars - 1) * self.bar_gap) +
                           self.bar_height)
        width = self.bar_width + 2 * self.bar_hmargin
        height = bar_area_height + self.bottom_height

        self.light_hgap = 0.9 * (width / (self.state.nlights + 1))
        self.first_light_x = (width -
                              (self.light_hgap * (self.state.nlights - 1))) / 2

        self.peg_vcenter_offset = (self.bar_height / 2)

        frame = Tkinter.Frame(tk, background=self.background,
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

        for i in range(0, self.state.npegs):
            x = self.first_peg_x + i * self.peg_gap
            self.create_ring(i, canvas, x, self.bar_ring_y,
                             self.ring_outer_radius,
                             self.sourcedata, self.sourcetag)

        for i in range(0, self.state.nlights):
            x = self.first_light_x + i * self.light_hgap
            self.create_ring(i, canvas, x, self.light_ring_y,
                             -self.ring_outer_radius,
                             self.destdata, self.desttag)
            self.create_light(canvas, i)

        canvas.tag_bind(self.movable, "<ButtonPress-1>", self.bar_set_cb)
        canvas.tag_bind(self.movable, "<B1-Motion>", self.bar_move_cb)
        canvas.tag_bind(self.pegtag, "<ButtonPress-1>", self.toggle_peg)
        canvas.tag_bind(self.sourcetag, "<ButtonPress-1>", self.start_line)
        canvas.tag_bind(self.sourcetag, "<B1-Motion>", self.move_line)
        canvas.tag_bind(self.sourcetag, "<ButtonRelease-1>", self.end_line)

    def draw_static_marks(self, canvas):
        for i in range(0, self.state.npegs):
            x = self.first_peg_x + i * self.peg_gap
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
            self.create_peg(canvas, grouptag, top, barnum, i)

    def create_peg(self, canvas, grouptag, top, barnum, pegnum):

        for dx in (-self.bar_delta, self.bar_delta):

            peg_x = self.first_peg_x + pegnum * self.peg_gap
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

    def create_ring(self, ringnum, canvas, x, y, voffset, pointdata, tag):
        data = (ringnum, x, y + voffset);
        item = canvas.create_oval(x - self.ring_outer_radius,
                                  y - self.ring_outer_radius,
                                  x + self.ring_outer_radius,
                                  y + self.ring_outer_radius,
                                  tags=tag,
                                  fill=self.ringcolor)
        pointdata[item] = data;
        item = canvas.create_oval(x - self.ring_inner_radius,
                                  y - self.ring_inner_radius,
                                  x + self.ring_inner_radius,
                                  y + self.ring_inner_radius,
                                  tags=tag,
                                  fill=self.ringholecolor)
        pointdata[item] = data;

    def create_light(self, canvas, lightnum):
        x = self.first_light_x + lightnum * self.light_hgap
        y = self.light_y
        if lightnum == 0:
            fill = self.redlightoff
        else:
            fill = self.greenlightoff
        canvas.create_oval(x - self.light_radius,
                           y - self.light_radius,
                           x + self.light_radius,
                           y + self.light_radius,
                           fill=fill)


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

    def start_line(self, event):
        canvas = event.widget
        item = canvas.find_withtag(Tkinter.CURRENT)[0]
        sourcedata = self.sourcedata[item]
        self.set_cur_line(canvas,
                          canvas.create_line(sourcedata[1], sourcedata[2],
                                             event.x, event.y,
                                             tags=self.linetag,
                                             capstyle="round",
                                             width=self.linewidth))
        canvas.tag_bind(self.linetag, "<ButtonPress-1>", self.continue_line)
        canvas.tag_bind(self.linetag, "<B1-Motion>", self.move_line)
        canvas.tag_bind(self.linetag, "<ButtonRelease-1>", self.end_line)

    def continue_line(self, event):
        canvas = event.widget
        self.set_cur_line(canvas, canvas.find_withtag(Tkinter.CURRENT)[0])
        x0, y0, x1, y1 = canvas.coords(self.cur_line)
        source = self.find_pointdata(canvas, x0, y0, self.sourcedata)
        dest = self.find_pointdata(canvas, x1, y1, self.destdata)
        if source == None:
            raise self.InternalError, "no source item"
        if dest == None:
            raise self.InternalError, "no dest item"
        self.move_line(event)
        self.state.set_patch(self.sourcedata[source][0],
                             self.destdata[dest][0],
                             -1)

    def move_line(self, event):
        canvas = event.widget
        coords = canvas.coords(self.cur_line)
        canvas.coords(self.cur_line, coords[0], coords[1], event.x, event.y)

    def end_line(self, event):
        canvas = event.widget
        x0, y0, x1, y1 = canvas.coords(self.cur_line)
        dest = self.find_pointdata(canvas, event.x, event.y, self.destdata)
        if dest:
            destdata = self.destdata[dest]
            canvas.coords(self.cur_line,
                          x0, y0, destdata[1], destdata[2])
            source = self.find_pointdata(canvas, x0, y0, self.sourcedata)
            if source == None:
                raise self.InternalError, "no source item"

            sourcenum = self.sourcedata[source][0]
            destnum = self.destdata[dest][0]
            self.state.set_patch(sourcenum, destnum, 1)

        else:
            canvas.delete(self.cur_line)

        self.set_cur_line(canvas, None)

    def find_pointdata(self, canvas, x, y, pointdata):
        items = canvas.find_overlapping(x - self.ring_outer_radius,
                                        y - self.ring_outer_radius,
                                        x + self.ring_outer_radius,
                                        y + self.ring_outer_radius)
        result = None
        for item in items:
            if pointdata.has_key(item):
                result = item
        return result

    def set_cur_line(self, canvas, item):
        if item != self.cur_line:
            if self.cur_line:
                canvas.itemconfigure(self.cur_line, fill=self.linecolor)
            self.cur_line = item
            if self.cur_line:
                canvas.lift(self.cur_line)
                canvas.itemconfigure(self.cur_line, fill=self.selectedlinecolor)


root = Tkinter.Tk()
root.title("JR01")
root.resizable(0, 0)
JR01Win(root, JR01State(3, 7, 4))
try:
    root.mainloop()
except KeyboardInterrupt:
    pass

