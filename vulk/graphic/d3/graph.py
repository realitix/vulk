from vulk import vulkanconstant as vc
from vulk.math import matrix
from vulk.graphic import uniform


class GraphContext():
    def __init__(self, context):
        self.context = context
        self.model_matrix = matrix.Matrix4()

        matrix_attribute = uniform.UniformAttribute(
            uniform.UniformShapeType.MATRIX4,
            vc.DataType.SFLOAT32)
        uniform_attributes = uniform.UniformAttributes([matrix_attribute])
        self.uniform_root = uniform.UniformBlock(context, uniform_attributes)


class Node():
    def __init__(self):
        self.children = []

    def update(self, context):
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

    def update(self, context):
        context.uniform_root.set_uniform(self.camera.combined.values)
        context.uniform_root.upload(context.context)


class ModelNode(Node):
    def __init__(self, model):
        super().__init__()
        self.model = model

    def update(self, context):
        self.model.render(context)
        super().update(context)


class TransformationNode(Node):
    def __init__(self, matrix):
        super().__init__()
        self.matrix = matrix

    def udpate(self, context):
        # Update push constant with model matrix
        pass
