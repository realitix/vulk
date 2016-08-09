class Material():
    def __init__(self, driver, attributes):
        self.shader_program = driver.get_shader(attributes)
        self.attributes = attributes
