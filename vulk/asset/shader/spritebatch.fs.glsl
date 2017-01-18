#version 450
#extension GL_ARB_separate_shader_objects : enable

// mat4 are accessed like a 2D array mat[x][y]
// with x the colum number and y the row number

layout(location = 0) in vec4 i_color;
layout(location = 1) in vec2 i_textureCoordinates;

layout(location = 0) out vec4 o_color;

layout(set = 0, binding = 1) uniform sampler2D u_texture;


void main() {
    o_color = i_color * texture(u_texture, i_textureCoordinates);
}
