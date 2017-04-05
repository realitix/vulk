#version 450
#extension GL_ARB_separate_shader_objects : enable

// borders are in the order [top, right, bottom, left]

layout(location = 0) in vec2 i_position;
layout(location = 1) in vec2 i_textureCoordinates;
layout(location = 2) in vec4 i_color;
layout(location = 3) in vec4 i_borderWidths;
layout(location = 4) in vec4 i_borderColors[4];
layout(location = 8) in vec4 i_borderRadius;

layout(location = 0) out vec4 o_color;
layout(location = 1) out vec2 o_textureCoordinates;
layout(location = 2) flat out vec4 o_borderWidths;
layout(location = 3) flat out vec4 o_borderColors[4];
layout(location = 7) flat out vec4 o_borderRadius;

layout(set = 0, binding = 0) uniform Uniform {
    mat4 u_combinedMatrix;
};

out gl_PerVertex {
    vec4 gl_Position;
};


void main() {
    o_color = i_color;
    o_borderWidths = i_borderWidths;
    o_borderRadius = i_borderRadius;
    o_borderColors = i_borderColors;
    o_textureCoordinates = i_textureCoordinates;

    gl_Position = u_combinedMatrix * vec4(i_position, 0., 1.);
}

