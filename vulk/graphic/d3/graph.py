class Node():
    def __init__(self):
        self.children = []

    def render(self, context):
        for child in self.children:
            child.update(context)

    def dispose(self):
        for child in self.children:
            child.dispose()
        self.children = []


class RootNode(Node):
    def __init__(self, camera):
        super().__init__()
        self.camera = camera

    def render(self, context):
        # update uniform buffer with constant values across the frame
        pass


class ModelNode(Node):
    def __init__(self, model):
        super().__init__()
        self.model = model

    def render(self, context):
        self.model.render(context)
        super().update(context)


class TransformationNode(Node):
    def __init__(self, matrix):
        super().__init__()
        self.matrix = matrix

    def render(self, context):
        # Update push constant with model matrix
        pass
