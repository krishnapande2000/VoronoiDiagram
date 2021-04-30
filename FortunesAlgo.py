import Tkinter as tk
import random
import math
import heapq
import itertools

class Site:

   def __init__(self, x, y):
       self.x = x
       self.y = y

class Event:
    
    def __init__(self, x, p, a):
        self.x = x
        self.p = p
        self.a = a
        self.valid = True

class Arc:

    def __init__(self, p, a=None, b=None):
        self.p = p
        self.pprev = a
        self.pnext = b
        self.e = None
        self.s0 = None
        self.s1 = None

class Segment:
    
    def __init__(self, p):
        self.start = p
        self.end = None
        self.done = False

    def finish(self, p):
        if not self.done:
	        self.end = p
	        self.done = True        

# class priority queue is taken from available codes online 
# and modified to use x-coordinate of the site as primary key
class PriorityQueue:

    def __init__(self):
        self.pq = []
        self.entry_finder = {}
        self.counter = itertools.count()

    def push(self, item):
        # check for duplicate
        if item in self.entry_finder: return
        count = next(self.counter)
        # use x-coordinate as a primary key (heapq in python is min-heap)
        entry = [item.x, count, item]
        self.entry_finder[item] = entry
        heapq.heappush(self.pq, entry)

    def pop(self):
        while self.pq:
            priority, count, item = heapq.heappop(self.pq)
            if item is not 'Removed':
                del self.entry_finder[item]
                return item
        raise KeyError('pop from an empty priority queue')

    def top(self):
        while self.pq:
            priority, count, item = heapq.heappop(self.pq)
            if item is not 'Removed':
                del self.entry_finder[item]
                self.push(item)
                return item
        raise KeyError('top from an empty priority queue')

    def empty(self):
        return not self.pq
            

class Fortunes:

    def __init__(self, points):
        
        self.points = PriorityQueue() # site events
        self.event = PriorityQueue() # circle events
        self.arc = None  # binary tree for parabola arcs
        self.output = [] # list of line segments of the final voronoi diagram


        # creating the bounding box
        self.left = 0
        self.right = 0
        self.up = 0
        self.down = 0

        # insert points to site event
        for pts in points:
            point = Site(pts[0], pts[1])
            self.points.push(point)
            # keep track of bounding box size
            if point.x < self.left: self.left = point.x
            if point.y < self.up: self.up = point.y
            if point.x > self.right: self.right = point.x
            if point.y > self.down: self.down = point.y

        # add margins to the bounding box
        deltax = (self.right - self.left + 1) / 4.0
        deltay = (self.down - self.up + 1) / 4.0
        self.left = self.left - deltax
        self.right = self.right + deltax
        self.up = self.up - deltay
        self.down = self.down + deltay


    def algorithm(self):
        while not self.points.empty():
            if not self.event.empty() and (self.event.top().x <= self.points.top().x):
            	# circle event
                self.process_event() # handle circle event
            else:
            	# site event 
                # get next event from site pq
		        p = self.points.pop()
		        # add new arc (parabola)
		        self.arc_insert(p) # handle site event

        # after all points, process remaining circle events
        while not self.event.empty():
            self.process_event()

        # complete all edges of the voronoi diagram finding intersections of the current beach line
        l = self.right + (self.right - self.left) + (self.down - self.up)
        i = self.arc
        while i.pnext is not None:
            if i.s1 is not None:
                p = self.intersection(i.p, i.pnext.p, l*2.0)
                i.s1.finish(p)
            i = i.pnext

        # create the result of the program in the form of an array of line segments
        res = []
        for o in self.output:
            p0 = o.start
            p1 = o.end
            res.append((p0.x, p0.y, p1.x, p1.y))
        return res    


    def process_event(self):
        # get next event from the priorirty queue of circles
        e = self.event.pop()

        if e.valid:
            # start new edge
            s = Segment(e.p)
            self.output.append(s)

            # remove associated arc (parabola)
            a = e.a
            if a.pprev is not None:
                a.pprev.pnext = a.pnext
                a.pprev.s1 = s
            if a.pnext is not None:
                a.pnext.pprev = a.pprev
                a.pnext.s0 = s

            # finish the edges before and after a
            if a.s0 is not None: a.s0.finish(e.p)
            if a.s1 is not None: a.s1.finish(e.p)

            # recheck circle events on either side of p
            if a.pprev is not None: self.check_circle_event(a.pprev)
            if a.pnext is not None: self.check_circle_event(a.pnext)

    def arc_insert(self, p):
        if self.arc is None:
            self.arc = Arc(p)
        else:
            # find the current arcs at p.y
            i = self.arc
            while i is not None:
                flag, z = self.intersect(p, i)
                if flag:
                    # new parabola intersects arc i
                    flag, zz = self.intersect(p, i.pnext)
                    if (i.pnext is not None) and (not flag):
                        i.pnext.pprev = Arc(i.p, i, i.pnext)
                        i.pnext = i.pnext.pprev
                    else:
                        i.pnext = Arc(i.p, i)
                    i.pnext.s1 = i.s1

                    # add p between i and i.pnext
                    i.pnext.pprev = Arc(p, i, i.pnext)
                    i.pnext = i.pnext.pprev

                    i = i.pnext # now i points to the new arc

                    # add new half-edges connected to i's endpoints
                    seg = Segment(z)
                    self.output.append(seg)
                    i.pprev.s1 = i.s0 = seg

                    seg = Segment(z)
                    self.output.append(seg)
                    i.pnext.s0 = i.s1 = seg

                    # check for new circle events around the new arc
                    self.check_circle_event(i)
                    self.check_circle_event(i.pprev)
                    self.check_circle_event(i.pnext)

                    return
                        
                i = i.pnext

            # if p never intersects an arc, append it to the list
            i = self.arc
            while i.pnext is not None:
                i = i.pnext
            i.pnext = Arc(p, i)
            
            # insert new segment between p and i
            x = self.left
            y = (i.pnext.p.y + i.p.y) / 2.0;
            start = Site(x, y)

            seg = Segment(start)
            i.s1 = i.pnext.s0 = seg
            self.output.append(seg)

    def check_circle_event(self, i):
        # look for a new circle event for arc i
        if (i.e is not None) and (i.e.x  != self.left):
            i.e.valid = False
        i.e = None

        if (i.pprev is None) or (i.pnext is None): return

        flag, x, o = False,None,None
        a,b,c = i.pprev.p, i.p, i.pnext.p

        # check if bc is a "right turn" from ab
        if ((b.x - a.x)*(c.y - a.y) - (c.x - a.x)*(b.y - a.y)) <= 0: 
        	# Joseph O'Rourke, Computational Geometry in C (2nd ed.) p.189
	        A = b.x - a.x
	        B = b.y - a.y
	        C = c.x - a.x
	        D = c.y - a.y
	        E = A*(a.x + b.x) + B*(a.y + b.y)
	        F = C*(a.x + c.x) + D*(a.y + c.y)
	        G = 2*(A*(c.y - b.y) - B*(c.x - b.x))

	        if (G != 0): 
		        # point o is the center of the circle
		        ox = 1.0 * (D*E - B*F) / G
		        oy = 1.0 * (A*F - C*E) / G

		        # o.x plus radius equals max x coord
		        x = ox + math.sqrt((a.x-ox)**2 + (a.y-oy)**2)
		        o = Site(ox, oy)
		        flag=True

        if flag and (x > self.left):
            i.e = Event(x, o, i)
            self.event.push(i.e)
        
    def intersect(self, p, i):
        # check whether a new parabola at point p intersect with arc i
        if (i is None): return False, None
        if (i.p.x == p.x): return False, None

        a = 0.0
        b = 0.0

        if i.pprev is not None:
            a = (self.intersection(i.pprev.p, i.p, 1.0*p.x)).y
        if i.pnext is not None:
            b = (self.intersection(i.p, i.pnext.p, 1.0*p.x)).y

        if (((i.pprev is None) or (a <= p.y)) and ((i.pnext is None) or (p.y <= b))):
            py = p.y
            px = 1.0 * ((i.p.x)**2 + (i.p.y-py)**2 - p.x**2) / (2*i.p.x - 2*p.x)
            res = Site(px, py)
            return True, res
        return False, None

    def intersection(self, p0, p1, l):
        # get the intersection of two parabolas
        p = p0
        if (p0.x == p1.x):
            py = (p0.y + p1.y) / 2.0
        elif (p1.x == l):
            py = p1.y
        elif (p0.x == l):
            py = p0.y
            p = p1
        else:
            # use quadratic formula
            z0 = 2.0 * (p0.x - l)
            z1 = 2.0 * (p1.x - l)

            a = 1.0/z0 - 1.0/z1;
            b = -2.0 * (p0.y/z0 - p1.y/z1)
            c = 1.0 * (p0.y**2 + p0.x**2 - l**2) / z0 - 1.0 * (p1.y**2 + p1.x**2 - l**2) / z1

            py = 1.0 * (-b-math.sqrt(b*b - 4*a*c)) / (2*a)
            
        px = 1.0 * (p.x**2 + (p.y-py)**2 - l**2) / (2*p.x-2*l)
        res = Site(px, py)
        return res

   
        


class CanvasWindow:
    # radius of drawn points on canvas
    RADIUS = 2

    # flag to lock the canvas when drawn
    FIX_POINTS = False
    
    def __init__(self, master):
        self.master = master
        self.master.title("Fortunes Algo to Draw Voronoi")

        self.frmMain = tk.Frame(self.master, relief=tk.RAISED, borderwidth=2)
        self.frmMain.pack(fill=tk.BOTH, expand=1)

        self.w = tk.Canvas(self.frmMain, width=700, height=500)
        self.w.config(background='white')
        self.w.bind('<Button-1>', self.onCanvasClick)
        self.w.pack()       

        self.frmButton = tk.Frame(self.master)
        self.frmButton.pack()
        
        self.btnVoronoi = tk.Button(self.frmButton, text='Voronoi',bg='cyan', width=50, command=self.onClickVoronoi)
        self.btnVoronoi.pack(side=tk.LEFT)
        
        self.btnClear = tk.Button(self.frmButton, text='Clear', bg='cyan',width=50, command=self.onClickClear)
        self.btnClear.pack(side=tk.LEFT)

    def onCanvasClick(self, event):
        if not self.FIX_POINTS:
            self.w.create_oval(event.x-self.RADIUS, event.y-self.RADIUS, event.x+self.RADIUS, event.y+self.RADIUS, fill="brown")
    
    def drawVoronoi(self, lines):
        for l in lines:
            self.w.create_line(l[0], l[1], l[2], l[3], fill='blue')
    
    def onClickVoronoi(self):
        if not self.FIX_POINTS:
            self.FIX_POINTS = True
        
            pObj = self.w.find_all()
            points = []
            for p in pObj:
                coord = self.w.coords(p)
                points.append((coord[0]+self.RADIUS, coord[1]+self.RADIUS))

            vp = Fortunes(points)
            lines = vp.algorithm()
            self.drawVoronoi(lines)
            
            print lines

    def onClickClear(self):
        self.FIX_POINTS = False
        self.w.delete(tk.ALL)

    
    
def main(): 
    root = tk.Tk()
    app = CanvasWindow(root)
    root.mainloop()

if __name__ == '__main__':
    main()
