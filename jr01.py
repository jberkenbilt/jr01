#!/usr/bin/env python
# -*-python-*-
#
# $Id: jr01.py,v 1.8 1999-07-11 00:27:35 ejb Exp $
# $Source: /work/cvs/jr01/jr01.py,v $
# $Author: ejb $
#

import Tkinter
import math

class JR01State:
    debug = 0

    def __init__(self, bars = 3, pegs = 7, lights = 4):
        if lights > pegs:
            lights = pegs

        self.nbars = bars
        self.npegs = pegs
        self.nlights = lights

        # pegs[barnum][pegnum][position] == peg_state
        self.pegs = []
        for bar in range(0, bars):
            self.pegs.append([])
            for peg in range(0, pegs):
                self.pegs[bar].append([])
                for position in (0, 1):
                    self.pegs[bar][peg].append(0)

        # bars[barnum] == position
        self.bars = []
        for bar in range(0, bars):
            self.bars.append(None)

        # patches[column][light] == patch_state
        self.patches = []
        for column in range(0, pegs):
            self.patches.append([])
            for light in range(0, lights):
                self.patches[column].append(0)

    def set_win(self, win):
        self.win = win;

    def set_peg_state(self, barnum, pegnum, position, state):
        if self.debug:
            print "set peg", (barnum, pegnum, position), "to state", state
        self.pegs[barnum][pegnum][position] = state
        self.win.update_peg(barnum,pegnum,position)

    def set_bar_position(self, barnum, position):
        if self.debug:
            print "set bar", barnum, "to position", position
        self.bars[barnum] = position

    def set_patch(self, source, dest, state):
        if self.debug:
            print "setting patch from column",
            print source, "to light", dest, "to", state
        if self.patches[source][dest] != state:
            self.patches[source][dest] = state
            if state:
                self.win.draw_patch_line(source, dest)

    def compute(self):
        # Initially, all lights are off.
        result = self.nlights * [0]

        if None not in self.bars:
            # Assume all columns are active.  "And" column with the peg
            # value for each column.
            for column in range(0, self.npegs):
                active = 1
                for bar in range(0, self.nbars):
                    position = self.bars[bar]
                    val = self.pegs[bar][column][position]
                    if self.debug:
                        print "column", column, "bar", bar,
                        print "position", position, "val", val
                    active = active & val
                if self.debug:
                    print "column", column, "active", active
                if active:
                    # Turn on any lights connected to this column
                    for light in range(0, self.nlights):
                        if self.patches[column][light]:
                            result[light] = 1
            
        return result

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
    redlighton = "#ad1010"
    greenlighton = "#3da829"
    pegcolor = "black"
    ringholecolor = "black"
    linecolor = "black"
    selectedlinecolor = "blue"
    compute_off_color = "#ccc"
    compute_on_color = "#888"

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
    linewidth = 6
    compute_radius = 20
    compute_x_from_right = 35
    compute_y_above_bottom = 35

    movabletag = "movable"
    bartag = "bar"
    pegtag = "peg"
    linetag = "line"
    sourcetag = "source"
    desttag = "dest"
    computetag = "compute"

    cur_line = None

    class Bar:
        def __init__(self, jr01_state, barnum):
            self.jr01_state = jr01_state
            self.barnum = barnum
            self.position = None

        def set_position(self, position):
            if self.position != position:
                self.position = position
                self.jr01_state.set_bar_position(self.barnum, position)


    class Peg:
        def __init__(self, jr01_state, barnum, pegnum, position, canvas,
                     outer_item, inner_item):
            self.jr01_state = jr01_state
            self.barnum = barnum
            self.pegnum = pegnum
            self.canvas = canvas
            self.outer_item = outer_item
            self.inner_item = inner_item
            self.position = position
            self.state = 0

        def update(self):
            if self.state:
                self.canvas.itemconfigure(self.outer_item,
                                          fill=JR01Win.pegcolor)
                self.canvas.itemconfigure(self.inner_item,
                                          fill=JR01Win.pegcolor)
            else:
                self.canvas.itemconfigure(self.outer_item,
                                          fill=JR01Win.barcolor)
                self.canvas.itemconfigure(self.inner_item,
                                          fill=JR01Win.barshadow)

        def toggle(self):
            self.state = 1 - self.state
            self.jr01_state.set_peg_state(self.barnum, self.pegnum,
                                          self.position, self.state)
            
    def __init__(self, tk, state):

        self.frame = Tkinter.Frame(tk, background=self.background,
                                   highlightthickness=20,
                                   highlightcolor=self.barcolor,
                                   highlightbackground=self.barcolor)
        self.frame.pack()

        button_frame = Tkinter.Frame(tk)

        open_button = Tkinter.Button(button_frame, text="open")
        open_button.pack(side=Tkinter.LEFT)
        save_button = Tkinter.Button(button_frame, text="save")
        save_button.pack(side=Tkinter.LEFT)
        reset_button = Tkinter.Button(button_frame, text="reset",
                                      command=self.reset)
        reset_button.pack(side=Tkinter.LEFT)
        quit_button = Tkinter.Button(button_frame, text="quit",
                                     command=tk.quit)
        quit_button.pack(side=Tkinter.LEFT)

        button_frame.pack()

        self.init(state)

    def init(self, state):
        self.state = state

        # Graphics state information
        
        # Each item with the "movable" tag is expected to have an
        # entry in move_sets.  The key is the item number, and the
        # value is a 2-tuple whose first value is the "main item" in
        # the move set and whose second item is a tag that identifies
        # all items in the move set.  The main item is the item whose
        # coordinates are used to enforce any constraints that may be
        # imposed upon moving the item.  The effect is that all items
        # in the same move_set are always moved together.
        self.move_sets = {}
        # maps a bar item to its corresponding Bar object
        self.bars = {}
        # maps a peg item to its corresponding Peg object
        self.pegs = {}
        # "sourcedata" and "destdata" store information for line drawing
        self.sourcedata = {}
        self.destdata = {}
        self.lights = []

        # Maps source column number to coordinates
        self.source_table = {}
        # Maps dest light number to coordinates
        self.dest_table = {}
        # Maps (barnum, pegnum, position) to Peg object
        self.peg_table = {}

        self.compute_geometry()
        self.create_canvas()
        self.state.set_win(self)

    def reset(self):
        self.canvas.destroy()
        self.init(JR01State(self.state.nbars,
                            self.state.npegs,
                            self.state.nlights))

    def create_canvas(self):
        self.canvas = Tkinter.Canvas(self.frame,
                                     width=self.width, height=self.height,
                                     background=self.bgcolor,
                                     borderwidth=0, highlightthickness=0,
                                     cursor="hand2")
        self.canvas.pack()

        self.draw_static_marks()

        for i in range(0, self.state.nbars):
            self.create_bar(i, self.first_bar_top + i * self.bar_gap)

        for i in range(0, self.state.npegs):
            x = self.first_peg_x + i * self.peg_gap
            self.create_ring(i, x, self.bar_ring_y,
                             self.ring_outer_radius,
                             self.sourcedata, self.source_table,
                             self.sourcetag)

        for i in range(0, self.state.nlights):
            x = self.first_light_x + i * self.light_hgap
            self.create_ring(i, x, self.light_ring_y,
                             -self.ring_outer_radius,
                             self.destdata, self.dest_table,
                             self.desttag)
            self.create_light(i)
        self.turn_lights_off()

        # Make a pentagonal compute button.
        pentagon = []
        degrad = 180.0/math.pi
        for angle in (range(54, 360, 72)):
            radians = angle/degrad
            sin = math.sin(radians)
            cos = math.cos(radians)
            x = self.compute_radius * cos + self.compute_x
            y = self.compute_radius * sin + self.compute_y
            pentagon.append(x)
            pentagon.append(y)

        self.compute_button = self.canvas.create_polygon(
            pentagon, tag=self.computetag,
            fill=self.compute_off_color)

        self.canvas.tag_bind(self.movabletag, "<ButtonPress-1>",
                             self.bar_set_cb)
        self.canvas.tag_bind(self.movabletag, "<B1-Motion>",
                             self.bar_move_cb)
        self.canvas.tag_bind(self.pegtag, "<ButtonPress-1>",
                             self.toggle_peg)
        self.canvas.tag_bind(self.sourcetag, "<ButtonPress-1>",
                             self.start_line)
        self.canvas.tag_bind(self.sourcetag, "<B1-Motion>",
                             self.move_line)
        self.canvas.tag_bind(self.sourcetag, "<ButtonRelease-1>",
                             self.end_line)
        self.canvas.tag_bind(self.computetag, "<ButtonPress-1>",
                             self.compute_down)
        self.canvas.tag_bind(self.computetag, "<ButtonRelease-1>",
                             self.compute_up)

    def compute_geometry(self):
        self.bar_width = (self.state.npegs + 1) * self.peg_gap
        self.bar_left = self.bar_hmargin
        self.bar_right = self.bar_hmargin + self.bar_width
        self.first_bar_top = self.bar_vmargin

        self.vline_top = self.bar_vmargin - self.vline_overhang
        self.vline_height = (self.bar_gap * (self.state.nbars - 1) +
                             self.bar_height +
                             2 * self.vline_overhang)
        self.bar_ring_y = (self.vline_top + self.vline_height +
                                self.ring_gap)
        self.light_ring_y = self.bar_ring_y + self.light_top_gap
        self.light_y = (self.light_ring_y + self.ring_gap +
                        self.light_radius)

        bar_area_height = ((2 * self.bar_vmargin) +
                           ((self.state.nbars - 1) * self.bar_gap) +
                           self.bar_height)
        self.width = self.bar_width + 2 * self.bar_hmargin
        self.height = bar_area_height + self.bottom_height

        self.compute_x = self.width - self.compute_x_from_right
        self.compute_y = self.height - self.compute_y_above_bottom

        self.light_hgap = 0.9 * (self.width / (self.state.nlights + 1))
        self.first_light_x = (self.width -
                              (self.light_hgap * (self.state.nlights - 1))) / 2

        self.peg_vcenter_offset = (self.bar_height / 2)

    def draw_static_marks(self):
        for i in range(0, self.state.npegs):
            x = self.first_peg_x + i * self.peg_gap
            self.canvas.create_line(x, self.vline_top,
                                    x, self.vline_top + self.vline_height,
                                    fill=self.markcolor)


    def create_bar(self, barnum, top):
        grouptag = self.bartag + "-" + `barnum`
        main_item = self.canvas.create_rectangle(
            self.bar_left, top,
            self.bar_right, self.bar_height + top,
            tags = (grouptag, self.movabletag),
            width = 2, fill = self.barcolor)
        self.move_sets[main_item] = (main_item, grouptag)
        handle = self.canvas.create_rectangle(
            self.bar_right - self.handle_width, top + 2,
            self.bar_right - 4, top + self.bar_height - 4,
            tags = (grouptag, self.movabletag),
            width = 0, fill=self.barshadow)
        self.move_sets[handle] = (main_item, grouptag)

        bar = self.Bar(self.state, barnum)
        self.bars[main_item] = bar
        self.bars[handle] = bar

        for i in range(0, self.state.npegs):
            self.create_peg(grouptag, top, barnum, i)

    def create_peg(self, grouptag, top, barnum, pegnum):

        for dx in (-self.bar_delta, self.bar_delta):

            peg_x = self.first_peg_x + pegnum * self.peg_gap
            peg_y = top + self.peg_vcenter_offset

            outer_item = self.canvas.create_oval(
                dx + peg_x - self.peg_outer_radius,
                peg_y - self.peg_outer_radius,
                dx + peg_x + self.peg_outer_radius,
                peg_y + self.peg_outer_radius,
                tags = (grouptag, self.pegtag),
                outline = "",
                fill=self.barcolor)
            
            inner_item = self.canvas.create_oval(
                dx + peg_x - self.peg_inner_radius,
                peg_y - self.peg_inner_radius,
                dx + peg_x + self.peg_inner_radius,
                peg_y + self.peg_inner_radius,
                tags = (grouptag, self.pegtag),
                fill=self.barshadow)

            if (dx > 0):
                position = 1
            else:
                position = 0

            peg = self.Peg(self.state, barnum, pegnum, position, self.canvas,
                           outer_item, inner_item)
            self.pegs[outer_item] = peg
            self.pegs[inner_item] = peg
            self.peg_table[(barnum, pegnum, position)] = peg

    def create_ring(self, ringnum, x, y, voffset, pointdata, point_table, tag):
        data = (ringnum, x, y + voffset)
        item = self.canvas.create_oval(
            x - self.ring_outer_radius,
            y - self.ring_outer_radius,
            x + self.ring_outer_radius,
            y + self.ring_outer_radius,
            tags=tag,
            fill=self.ringcolor)
        pointdata[item] = data
        item = self.canvas.create_oval(
            x - self.ring_inner_radius,
            y - self.ring_inner_radius,
            x + self.ring_inner_radius,
            y + self.ring_inner_radius,
            tags=tag,
            fill=self.ringholecolor)
        pointdata[item] = data
        point_table[ringnum] = data[1:3]

    def create_light(self, lightnum):
        x = self.first_light_x + lightnum * self.light_hgap
        y = self.light_y
        self.lights.append(
            self.canvas.create_oval(x - self.light_radius,
                                    y - self.light_radius,
                                    x + self.light_radius,
                                    y + self.light_radius))

    def toggle_peg(self, event):
        item = self.canvas.find_withtag(Tkinter.CURRENT)[0]
        if self.pegs.has_key(item):
            peg = self.pegs[item]
            peg.toggle()

    def bar_set_cb(self, event):
        self.last_x = event.x

    def bar_move_cb(self, event):
        item = self.canvas.find_withtag(Tkinter.CURRENT)[0]

        items = (item,)
        coords = self.canvas.coords(item)

        bar = None
        if (self.bars.has_key(item)):
            bar = self.bars[item]

        if self.move_sets.has_key(item):
            coords = self.canvas.coords(self.move_sets[item][0])
            items = self.canvas.find_withtag(self.move_sets[item][1])

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
                bar.set_position(1)
            elif newleft == maxleft:
                bar.set_position(0)
            else:
                bar.set_position(None)

        for item in items:
            self.canvas.move(item, dx, 0)

        self.last_x = self.last_x + dx

    def start_line(self, event):
        item = self.canvas.find_withtag(Tkinter.CURRENT)[0]
        sourcedata = self.sourcedata[item]
        self.set_cur_line(self.create_patch_line(
            sourcedata[1], sourcedata[2],
            event.x, event.y, self.selectedlinecolor))
        self.canvas.tag_bind(self.linetag, "<ButtonPress-1>",
                             self.continue_line)
        self.canvas.tag_bind(self.linetag, "<B1-Motion>", self.move_line)
        self.canvas.tag_bind(self.linetag, "<ButtonRelease-1>", self.end_line)

    def continue_line(self, event):
        self.set_cur_line(self.canvas.find_withtag(Tkinter.CURRENT)[0])
        x0, y0, x1, y1 = self.canvas.coords(self.cur_line)
        source = self.find_pointdata(x0, y0, self.sourcedata)
        dest = self.find_pointdata(x1, y1, self.destdata)
        if source == None:
            raise self.InternalError, "no source item"
        if dest == None:
            raise self.InternalError, "no dest item"
        self.move_line(event)
        self.state.set_patch(self.sourcedata[source][0],
                             self.destdata[dest][0], 0)

    def move_line(self, event):
        coords = self.canvas.coords(self.cur_line)
        self.canvas.coords(self.cur_line,
                           coords[0], coords[1], event.x, event.y)

    def end_line(self, event):
        x0, y0, x1, y1 = self.canvas.coords(self.cur_line)
        dest = self.find_pointdata(event.x, event.y, self.destdata)
        if dest:
            destdata = self.destdata[dest]
            self.canvas.coords(self.cur_line,
                               x0, y0, destdata[1], destdata[2])
            source = self.find_pointdata(x0, y0, self.sourcedata)
            if source == None:
                raise self.InternalError, "no source item"

            sourcenum = self.sourcedata[source][0]
            destnum = self.destdata[dest][0]
            # This routine cauase a new line to be drawn
            self.state.set_patch(sourcenum, destnum, 1)

        self.canvas.delete(self.cur_line)
        self.set_cur_line(None)

    def compute_down(self, event):
        self.canvas.itemconfigure(self.compute_button,
                                  fill=self.compute_on_color)
        self.set_lights(self.state.compute())

    def compute_up(self, event):
        self.canvas.itemconfigure(self.compute_button,
                                  fill=self.compute_off_color)
        self.turn_lights_off()

    def find_pointdata(self, x, y, pointdata):
        items = self.canvas.find_overlapping(x - self.ring_outer_radius,
                                             y - self.ring_outer_radius,
                                             x + self.ring_outer_radius,
                                             y + self.ring_outer_radius)
        result = None
        for item in items:
            if pointdata.has_key(item):
                result = item
        return result

    def set_cur_line(self, item):
        if item != self.cur_line:
            self.cur_line = item
            if self.cur_line:
                self.canvas.lift(self.cur_line)
                self.canvas.itemconfigure(self.cur_line,
                                          fill=self.selectedlinecolor)

    def update_peg(self, barnum, pegnum, position):
        self.peg_table[(barnum,pegnum,position)].update()

    def draw_patch_line(self, source, dest):
        x0, y0 = self.source_table[source]
        x1, y1 = self.dest_table[dest]
        self.create_patch_line(x0, y0, x1, y1, self.linecolor)
        pass

    def create_patch_line(self, x0, y0, x1, y1, fill):
        return self.canvas.create_line(
            x0, y0, x1, y1,
            tags=self.linetag,
            capstyle="round",
            width=self.linewidth,
            fill=fill)

    def set_lights(self, lightdata):
        for i in range(0, len(lightdata)):
            if i == 0:
                on = self.redlighton
                off = self.redlightoff
            else:
                on = self.greenlighton
                off = self.greenlightoff
            if (lightdata[i]):
                fill = on
            else:
                fill = off
            self.canvas.itemconfigure(self.lights[i], fill=fill)

    def turn_lights_off(self):
        self.set_lights([0] * self.state.nlights)
        
root = Tkinter.Tk()
root.title("JR01")
root.resizable(0, 0)
JR01Win(root, JR01State(3, 7, 4))
try:
    root.mainloop()
except KeyboardInterrupt:
    pass
