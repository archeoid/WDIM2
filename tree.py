import skia

FONT = skia.Font(skia.Typeface('Serif'), 48)
PADDING_X = 60
PADDING_Y = 100

TITLE_FONT = skia.Font(skia.Typeface('Serif'), 96)
TITLE_HEIGHT = 120

# ⠀⠀⢀⣀⠤⠿⢤⢖⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
# ⡔⢩⠂⠀⠒⠗⠈⠀⠉⠢⠄⣀⠠⠤⠄⠒⢖⡒⢒⠂⠤⢄⠀⠀⠀⠀
# ⠇⠤⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀⠈⠀⠈⠈⡨⢀⠡⡪⠢⡀⠀
# ⠈⠒⠀⠤⠤⣄⡆⡂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠢⠀⢕⠱⠀
# ⠀⠀⠀⠀⠀⠈⢳⣐⡐⠐⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠀⠁⠇
# ⠀⠀⠀⠀⠀⠀⠀⠑⢤⢁⠀⠆⠀⠀⠀⠀⠀⢀⢰⠀⠀⠀⡀⢄⡜⠀
# ⠀⠀⠀⠀⠀⠀⠀⠀⠘⡦⠄⡷⠢⠤⠤⠤⠤⢬⢈⡇⢠⣈⣰⠎⠀⠀
# ⠀⠀⠀⠀⠀⠀⠀⠀⠀⣃⢸⡇⠀⠀⠀⠀⠀⠈⢪⢀⣺⡅⢈⠆⠀⠀
# ⠀⠀⠀⠀⠀⠀⠀⠶⡿⠤⠚⠁⠀⠀⠀⢀⣠⡤⢺⣥⠟⢡⠃⠀⠀⠀
#⠀ ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠉⠀⠀⠀⠀⠀⠀⠀⠀

class Node:
    def __init__(self, label):
        self.bound = skia.Rect()
        self.position = skia.Point(0.0,0.0)
        self.children = []
        self.label = label
        self.extent = skia.Rect()

        FONT.measureText(label, bounds=self.extent)
        self.extent.offsetTo(0,0)
    
    def make_leaf(self):
        FONT.measureText(self.label, bounds=self.bound)
        self.bound.offsetTo(0,0)
    
    def add_child(self, child):
        self.children += [child]
        children_width = sum([c.bound.width() + PADDING_X for c in self.children]) - PADDING_X
        children_height = max([c.bound.height() for c in self.children])

        width = max(self.extent.width(), children_width)
        height = self.extent.height() + children_height + PADDING_Y

        self.bound = skia.Rect.MakeWH(width, height)
    
    def layout(self):
        for c in self.children:
            c.layout()

        if len(self.children) <= 1:
            position = self.bound.width()/2
            if self.extent.width() < self.bound.width():
                position = self.children[0].position.x()
            self.position = skia.Point(position, 0)
        if len(self.children) == 2:
            position = self.children[0].bound.width() + PADDING_X/2
            self.position = skia.Point(position, 0)
        if len(self.children) >= 2:
            position = 0.0
            offset = 0

            for c in self.children:
                position += c.position.x() + offset
                offset += c.bound.width() + PADDING_X

            position /= len(self.children)
            self.position = skia.Point(position, 0)

def build(derivation):
    if 'daughters' in derivation:
        node = Node(derivation['entity'])
        for c in derivation['daughters']:
            node.add_child(build(c))
        return node
    else:
        node = Node(derivation['entity'])
        if 'form' in derivation:
            leaf = Node(derivation['form'])
            leaf.make_leaf()
            node.add_child(leaf)
        else:
            node.make_leaf()
        return node

def truncate(text, font, width):
    glyphs = font.textToGlyphs(text)
    positions = font.getXPos(glyphs)
    elide_at = None
    for i, p in enumerate(positions):
        if p > width:
            elide_at = i
            break
    if elide_at:
        return text[0:elide_at-3] + "..."
    
    return text

def draw_line(canvas, p0, p1):
    paint = skia.Paint(AntiAlias=True, StrokeWidth=4.1, Style=skia.Paint.kStroke_Style)
    canvas.drawLine(p0, p1, paint)

def draw_rect(canvas, rect):
    paint = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style)
    canvas.drawRect(rect, paint)

def draw_text(canvas, text, x, y):
    bound = skia.Rect()
    FONT.measureText(text, bounds=bound)
    paint = skia.Paint(AntiAlias=True)
    canvas.drawString(text, x-bound.x(), y-bound.y(), FONT, paint)

def draw_title(canvas, title, width):
    title = truncate(title, TITLE_FONT, width-2*PADDING_X)

    bounds = skia.Rect()
    TITLE_FONT.measureText(title, bounds=bounds)

    x = (width-bounds.width())/2
    y = (TITLE_HEIGHT-bounds.height())/2

    paint = skia.Paint(AntiAlias=True)
    canvas.drawString(title, x, y+bounds.height(), TITLE_FONT, paint)

def draw(canvas, node, position):
    bound = node.bound.makeOffset(position)
    extent = node.extent.makeOffset(position + node.position)
    extent.offset(-extent.width()/2, 0)
    p0 = position + node.position
    p0.offset(0, extent.height()+5)

    #draw_rect(canvas, bound)
    #draw_rect(canvas, extent)
    draw_text(canvas, node.label, extent.x(), extent.y())

    position.offset(0, node.extent.height() + PADDING_Y)


    if len(node.children) == 1:
        child_width = node.children[0].bound.width()
        width = node.bound.width()
        if child_width < width:
            position.offset((width-child_width)/2, 0)

    for c in node.children:
        p1 = position + c.position
        p1.offset(0, -5)
        draw_line(canvas, p0, p1)
        
        draw(canvas, c, skia.Point(position.x(), position.y()))
        position.offset(c.bound.width() + PADDING_X, 0)

def render(prompt, derivation, out):
    root = build(derivation)
    root.layout()

    width, height = root.bound.width() + PADDING_X, root.bound.height() + PADDING_Y

    surface = skia.Surface(int(width + PADDING_X), int(height + TITLE_HEIGHT))
    canvas = surface.getCanvas()
    canvas.clear(0xFFFFFFFF)

    draw(canvas, root, skia.Point(PADDING_X, TITLE_HEIGHT + PADDING_Y/2))
    draw_title(canvas, prompt, width+PADDING_X)

    #canvas.scale(2, 2)
    image = surface.makeImageSnapshot()
    image.save(out, skia.kPNG)