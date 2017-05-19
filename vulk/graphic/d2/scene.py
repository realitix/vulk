'''This module contains scene related functions and classes'''
from functools import partial
from os import path
import logging

from vulk import PATH_VULK_SHADER
from vulk import vulkanconstant as vc
from vulk import vulkanobject as vo
from vulk.exception import VulkError
from vulk.math.shape import Rectangle
from vulk.math.interpolation import Linear
from vulk.graphic.d2.batch import SpriteBatch, BlockBatch, BlockProperty
from vulk.graphic.d2.font import TextRenderer

logger = logging.getLogger()


# ----------
# WIDGETS
# ----------
class PlaceMixin():
    """Mixin to place widget with absolute position"""
    def __init__(self):
        super().__init__()  # need super for MRO

    def place(self, width, height, x=0, y=0):
        self.parent.add_child_to_place(self, width, height, x, y)
        self.relocate = partial(self.place, width=width,
                                height=height, x=x, y=y)
        self.reload_location()

    def add_child_to_place(self, child, width, height, x, y):
        self.children.append(child)
        child.shape.set(Rectangle(self.shape.x + x, self.shape.y + y,
                                  width, height))


class GridMixin():
    """Mixin to place widget in a table"""
    def __init__(self):
        super().__init__()  # need super for MRO
        self.children_grid = {}
        self.columns = 1
        self.rows = 1

    def grid(self, column=0, row=0):
        self.parent.add_child_to_grid(self, column, row)
        self.relocate = partial(self.grid, column=column, row=row)
        self.reload_location()

    @property
    def column_width(self):
        return self.shape.width / self.columns

    @property
    def row_width(self):
        return self.shape.height / self.rows

    def add_child_to_grid(self, child, column, row):
        """Called when the child ask a place in the parent grid"""
        # Increase columns and rows number
        self.update_grid_size(column, row)

        # Register child
        self.register_child_grid(child, column, row)

        # Reshape all children
        self.reshape_grid()

    def reshape_grid(self):
        for child, grid_position in self.children_grid.items():
            x, y = self.grid_position_to_xy(grid_position)
            child.shape.set(Rectangle(x, y, self.column_width, self.row_width))

    def update_grid_size(self, column, row):
        if column >= self.columns:
            self.columns = column + 1
        if row >= self.rows:
            self.rows = row + 1

    def register_child_grid(self, child, column, row):
        # Remove child at grid position if exists
        existing_child = None
        for key, value in self.children_grid.items():
            if value == (column, row):
                existing_child = key

        if existing_child:
            self.children.remove(existing_child)
            self.children_grid.pop(existing_child)

        self.children_grid[child] = (column, row)
        self.children.append(child)

    def grid_position_to_xy(self, grid_position):
        return (self.shape.x + grid_position[0] * self.column_width,
                self.shape.y + grid_position[1] * self.row_width)


class Widget(PlaceMixin, GridMixin):
    """Widget is the base of the scene

    All widgets inherit from this class.
    """
    def __init__(self, parent):
        self.parent = parent
        self.children = []
        self.shape = Rectangle()
        self.color = [1, 1, 1, 1]  # rgba depending on parent color
        self.rotation = 0
        self.actions = []
        self.relocate = None  # partial function which relocates

        super().__init__()

    def reload_location(self):
        for child in self.children:
            if child.relocate:
                child.relocate()

    @property
    def x_rel(self):
        if self.parent:
            return self.parent.shape.x - self.shape.x
        return self.shape.x

    @property
    def y_rel(self):
        if self.parent:
            return self.parent.shape.y - self.shape.y
        return self.shape.y

    @property
    def color_abs(self):
        """Absolute color (not depending on parent color)"""
        if self.parent:
            pc = self.parent.color_abs
            return [c1 * c2 for c1, c2 in zip(pc, self.color)]

        return self.color

    @property
    def alpha(self):
        if self.parent:
            return self.parent.alpha * self.color[3]
        return self.color[3]

    @alpha.setter
    def alpha(self, value):
        self.color[3] = value

    def collect_children(self):
        """Return all chidren recursively"""
        result_children = self.children.copy()
        for child in self.children:
            result_children += child.collect_children()

        return result_children

    def reshape(self):
        self.reshape_grid()

    def reshape_all(self):
        """Ascend all parent until root and ask to reshape all"""
        if self.parent:
            self.parent.reshape_all()
            return

        self.reshape()

    def add_action(self, action):
        """Add action to the widget

        Actions are executed when you call `update`.
        Be careful, don't use the same action across several widgets,
        create a new action each time. Actions are initialized for
        each widget, if you reuse the same action, it will be initialized
        two times and the first widget will loose the action

        Args:
            action (Action): Action to perform
        """
        action.init(self)
        self.actions.append(action)

    def remove_action(self, action):
        if action in self.actions:
            action.unset_widget()
            self.actions.remove(action)

    def update(self, delta):
        """Method allowing to perform actions"""
        remove_actions = []
        for action in self.actions:
            # action.update return false if action is finished
            if not action.update(delta):
                remove_actions.append(action)

        for action in remove_actions:
            self.actions.remove(action)

        for child in self.children:
            child.update(delta)

    def get_renderer_name(self):
        """No renderer by default"""
        return None

    def render(self, renderer):
        """Render the widget

        Args:
            renderer: Renderer which can render this widget
        """
        pass


class Scene(Widget):
    '''Main 2D Scene'''
    def __init__(self, context, width, height, renderers=None):
        """Construct a new Scene

        Args:
            context (VulkContext)
            width (int): Scene width
            height (int): Scene height
        """
        super().__init__(None)
        self.shape.width = width
        self.shape.height = height

        # Default renderers
        self.renderers = {
            'default': SpriteBatch(context),
            'block': BlockBatch(context),
            'text': TextRenderer(context)
        }

        # Custom renderers
        if renderers:
            self.renderers.update(renderers)

    def _get_block_sp(self, context):
        """Create the `block` shader program

        Args:
            context (VulkContext)

        Returns:
            ShaderProgram
        """
        vs = path.join(PATH_VULK_SHADER, "block.vs.glsl")
        fs = path.join(PATH_VULK_SHADER, "block.fs.glsl")

        shaders_mapping = {
            vc.ShaderStage.VERTEX: vs,
            vc.ShaderStage.FRAGMENT: fs
        }

        return vo.ShaderProgramGlslFile(context, shaders_mapping)

    def render(self, context):
        """Render Scene

        For each widget, get renderer and render it.

        Args:
            context (VulkContext)

        Returns:
            Semaphore or None if no semaphore
        """
        widgets = self.collect_children()
        semaphores = None
        for widget in widgets:
            try:
                renderer = self.renderers[widget.get_renderer_name()]
            except KeyError:
                msg = ("Cannot find renderer")
                logger.critical(msg)
                raise VulkError(msg)

            renderer.begin(context, semaphores)
            widget.render(renderer)
            semaphores = [renderer.end()]

        return semaphores[0] if semaphores else None

    def update(self, delta):
        widgets = self.collect_children()
        for widget in widgets:
            widget.update(delta)


class BatchedScene(Scene):
    """Faster Scene but with limitations

    If your scene doesnét contain overlapping elements,
    this scene will be faster.
    """
    def render(self, context):
        """Render Scene

        Collect renderers and then display all widget by renderer.
        Renderers are in this order:
            - Block renderer
            - Sprite renderer
            - Text renderer

        Args:
            context (VulkContext)

        Returns:
            Semaphore or None if no semaphore
        """
        mapping = self.collect_widgets_to_render()
        semaphore = None
        for renderer, widgets in mapping.items():
            semaphores = [semaphore] if semaphore else []
            renderer.begin(context, semaphores)
            for widget in widgets:
                widget.render(renderer)
            semaphore = renderer.end()

        return semaphore if semaphore else None

    def collect_widgets_to_render(self):
        """Return a mapping used to render widgets

        Returns:
            dict[renderer: list[widgets]]
        """
        mapping = {}

        widgets = self.collect_children()
        for renderer_name, renderer in self.renderers.items():
            for widget in widgets:
                if widget.get_renderer_name() == renderer_name:
                    if not mapping.get(renderer):
                        mapping[renderer] = []

                    mapping[renderer].append(widget)

        return mapping


class Image(Widget):
    def __init__(self, parent, texture_region):
        """Construct a new Image widget

        Args:
            parent (Widget): Parent widget (may be a Scene)
            texture_region (TextureRegion): Region of the texture to draw
        """
        super().__init__(parent)
        self.texture_region = texture_region

    def get_renderer_name(self):
        return 'default'

    def render(self, renderer):
        """
        Args:
            renderer (SpriteBatch)
        """
        c = self.color_abs
        renderer.draw(self.texture_region.texture, self.shape.x,
                      self.shape.y, self.shape.width, self.shape.height,
                      r=c[0], g=c[1], b=c[2], a=c[3])


class Block(Widget):
    """Widget using the shader 'block' with allow lot of customization"""
    def __init__(self, parent, border_colors=None, border_widths=None):
        if not border_colors:
            border_colors = [[0.]*4]*4
        if not border_widths:
            border_widths = [0.]*4

        self.properties = BlockProperty()
        self.properties.colors = [[1.]*4]*4
        self.properties.border_colors = border_colors
        self.properties.border_widths = border_widths

        super().__init__(parent)

    def get_renderer_name(self):
        return 'block'

    def render(self, renderer):
        """
        Args:
            renderer (BlockBatch)
        """
        self.properties.colors[0][:] = self.color_abs[:]
        self.properties.colors[1][:] = self.color_abs[:]
        self.properties.colors[2][:] = self.color_abs[:]
        self.properties.colors[3][:] = self.color_abs[:]
        self.properties.width = self.shape.width
        self.properties.height = self.shape.height
        self.properties.x = self.shape.x
        self.properties.y = self.shape.y
        self.properties.rotation = self.rotation

        renderer.draw(self.properties)


class Label(Widget):
    """Widget used to write text"""
    def __init__(self, parent, fontdata, text):
        """Construct a new label widget

        Args:
            parent (Widget): Parent widget (may be a Scene)
            fontdata (FontData): Font to render
            text (str): Text to write
        """
        super().__init__(parent)
        self.text = text
        self.fontdata = fontdata

    def get_renderer_name(self):
        return 'text'

    def render(self, renderer):
        """
        Args:
            renderer (TextRenderer)
        """
        c = self.color_abs
        size = 30
        renderer.draw(self.fontdata, self.text, self.shape.x, self.shape.y,
                      size, r=c[0], g=c[1], b=c[2], a=c[3],
                      rotation=self.rotation)


# ----------
# ACTIONS
# ----------
class Action():
    def __init__(self):
        self.widget = None

    def init(self, widget):
        """Init action from widget"""
        self.widget = widget


class TemporalAction(Action):
    def __init__(self, duration, interpolation):
        super().__init__()

        if not interpolation:
            interpolation = Linear()

        self.duration = duration
        self.interpolation = interpolation
        self.time = 0

    def init(self, widget):
        super().init(widget)
        self.time = 0

    def update(self, delta):
        self.time += delta

        if self.percent() >= 1:
            return False

        return True

    def percent(self):
        return self.time / self.duration


class MoveTo(TemporalAction):
    def __init__(self, x, y, duration, interpolation=None):
        super().__init__(duration, interpolation)
        self.x_src = 0
        self.y_src = 0
        self.x_dest = x
        self.y_dest = y
        self._dest_init = False

    def init(self, widget):
        super().init(widget)

        self.x_src = widget.shape.x
        self.y_src = widget.shape.y

        if widget.parent and not self._dest_init:
            self._dest_init = True
            self.x_dest += widget.parent.shape.x
            self.y_dest += widget.parent.shape.y

    def update(self, delta):
        super().update(delta)

        percent = self.percent()
        if percent >= 1:
            return False

        percent = self.interpolation.apply(percent)
        x_current = self.x_src + (self.x_dest - self.x_src) * percent
        y_current = self.y_src + (self.y_dest - self.y_src) * percent

        self.widget.shape.x = x_current
        self.widget.shape.y = y_current

        return True


class MoveBy(TemporalAction):
    def __init__(self, x, y, duration, interpolation=None):
        super().__init__(duration, interpolation)
        self.x_width = x
        self.y_width = y
        self.x_prev = 0
        self.y_prev = 0

    def init(self, widget):
        super().init(widget)

        self.x_prev = 0
        self.y_prev = 0

    def _compute_move(self, percent):
        x_diff = self.x_width * percent
        y_diff = self.y_width * percent
        x_res = x_diff - self.x_prev
        y_res = y_diff - self.y_prev
        self.x_prev = x_diff
        self.y_prev = y_diff

        return x_res, y_res

    def update(self, delta):
        super().update(delta)

        percent = self.percent()
        if percent >= 1:
            return False

        x_rel, y_rel = self._compute_move(self.interpolation.apply(percent))
        self.widget.shape.x += x_rel
        self.widget.shape.y += y_rel

        return True


class RotateTo(TemporalAction):
    def __init__(self, rotation, duration, interpolation=None):
        super().__init__(duration, interpolation)
        self.rotation_src = 0
        self.rotation_dest = rotation
        self._dest_init = False

    def init(self, widget):
        super().init(widget)

        self.rotation_src = widget.rotation

        if widget.parent and not self._dest_init:
            self._dest_init = True
            self.rotation_dest += widget.parent.rotation

    def update(self, delta):
        super().update(delta)

        percent = self.percent()
        if percent >= 1:
            return False

        percent = self.interpolation.apply(percent)
        rotation_current = (self.rotation_src +
                            (self.rotation_dest - self.rotation_src) *
                            percent)
        self.widget.rotation = rotation_current

        return True


class RotateBy(TemporalAction):
    def __init__(self, rotation, duration, interpolation=None):
        super().__init__(duration, interpolation)
        self.rotation_base = rotation
        self.rotation_prev = 0

    def init(self, widget):
        super().init(widget)
        self.rotation_prev = 0

    def _compute_move(self, percent):
        rotation_diff = self.rotation_base * percent
        rotation_res = rotation_diff - self.rotation_prev
        self.rotation_prev = rotation_diff
        return rotation_res

    def update(self, delta):
        super().update(delta)

        percent = self.percent()
        if percent >= 1:
            return False

        rotation_rel = self._compute_move(self.interpolation.apply(percent))
        self.widget.rotation += rotation_rel

        return True


class FadeIn(TemporalAction):
    def __init__(self, duration, interpolation=None):
        super().__init__(duration, interpolation)
        self.fade_src = 0

    def init(self, widget):
        super().init(widget)
        self.fade_src = widget.alpha

    def update(self, delta):
        super().update(delta)

        percent = self.percent()
        if percent >= 1:
            return False

        percent = self.interpolation.apply(percent)
        self.widget.alpha = self.fade_src + (1 - self.fade_src) * percent

        return True


class FadeOut(TemporalAction):
    def __init__(self, duration, interpolation=None):
        super().__init__(duration, interpolation)
        self.fade_src = 0

    def init(self, widget):
        super().init(widget)
        self.fade_src = widget.alpha

    def update(self, delta):
        super().update(delta)

        percent = self.percent()
        if percent >= 1:
            return False

        percent = self.interpolation.apply(percent)
        self.widget.alpha = self.fade_src - self.fade_src * percent

        return True


class FadeTo(TemporalAction):
    def __init__(self, fade, duration, interpolation=None):
        super().__init__(duration, interpolation)
        self.fade_src = 0
        self.fade_dst = fade

    def init(self, widget):
        super().init(widget)
        self.fade_src = widget.alpha

    def update(self, delta):
        super().update(delta)

        percent = self.percent()
        if percent >= 1:
            return False

        percent = self.interpolation.apply(percent)
        a = self.fade_src + (self.fade_dst - self.fade_src) * percent
        self.widget.alpha = a

        return True


class Composite(Action):
    def __init__(self, actions):
        """
        actions: list of Action
        """
        super().__init__()
        self.actions_src = actions
        self.actions = None

    def init(self, widget):
        super().init(widget)
        self.actions = self.actions_src.copy()


class Sequence(Composite):
    def __init__(self, actions):
        """
        actions: list of Action
        """
        super().__init__(actions)
        self.current_action = None

    def next_action(self):
        try:
            self.current_action = self.actions.pop(0)
            self.current_action.init(self.widget)
        except IndexError:
            return False

        return True

    def update(self, delta):
        if not self.current_action and not self.next_action():
            return False

        if not self.current_action.update(delta) and not self.next_action():
            return False

        return True


class Parallel(Composite):
    def init(self, widget):
        super().init(widget)

        for action in self.actions:
            action.init(widget)

    def update(self, delta):
        self.actions = [a for a in self.actions if a.update(delta)]

        if not self.actions:
            return False

        return True


class Repeat(Action):
    def __init__(self, action, count=0):
        """
        if count = 0: Action is looping forever
        """
        super().__init__()
        self.action = action
        self.count = count
        self.current_count = 1

    def init(self, widget):
        super().init(widget)
        self.action.init(widget)

    def restart_action(self):
        self.action.init(self.widget)

    def update(self, delta):
        if self.action.update(delta):
            return True

        if self.current_count == self.count:
            return False

        self.current_count += 1
        self.restart_action()
        return True
