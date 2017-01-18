#version 450
#extension GL_ARB_separate_shader_objects : enable

layout(location = 0) in vec2 i_position;
layout(location = 1) in vec2 i_textureCoordinates;
layout(location = 2) in vec4 i_color;

layout(location = 0) out vec4 o_color;
layout(location = 1) out vec2 o_textureCoordinates;

layout(set = 0, binding = 0) uniform Uniform {
    mat4 u_combinedMatrix;
};

out gl_PerVertex {
    vec4 gl_Position;
};


void main() {
    o_color = i_color;
    o_textureCoordinates = i_textureCoordinates;
    gl_Position = u_combinedMatrix * vec4(i_position, 0., 1.);
}

