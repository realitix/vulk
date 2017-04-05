#version 450
#extension GL_ARB_separate_shader_objects : enable

// mat4 are accessed like a 2D array mat[x][y]
// with x the colum number and y the row number

layout(location = 0) in vec4 i_color;
layout(location = 1) in vec2 i_textureCoordinates;
layout(location = 2) flat in vec4 i_borderWidths;
layout(location = 3) flat in vec4 i_borderColors[4];
layout(location = 7) flat in vec4 i_borderRadius;

layout(location = 0) out vec4 o_color;


float isBorderLeft() {
    return step(i_textureCoordinates[0], i_borderWidths[3]);
}

float isBorderRight() {
    return step(1. - i_textureCoordinates[0], i_borderWidths[1]);
}

float isBorderTop() {
    return step(i_textureCoordinates[1], i_borderWidths[0]);
}

float isBorderBottom() {
    return step(1. - i_textureCoordinates[1], i_borderWidths[2]);
}

// Return the border color or vec4(0)
vec4 getBorderColor() {
    vec4 result = vec4(0.);
    result = mix(result, i_borderColors[0], isBorderTop() * i_borderColors[0].a);
    result = mix(result, i_borderColors[1], isBorderRight() * i_borderColors[1].a);
    result = mix(result, i_borderColors[2], isBorderBottom() * i_borderColors[2].a);
    result = mix(result, i_borderColors[3], isBorderLeft() * i_borderColors[3].a);

    return result;
}

// Return the border radius as vec4(0) or vec4(1)
vec4 getBorderRadius() {
    const vec4 hide = vec4(0.);
    vec4 result = vec4(1.);

    float topLeftDst = distance(i_textureCoordinates, vec2(i_borderRadius[0]));
    float topRightDst = distance(i_textureCoordinates, vec2(1.0 - i_borderRadius[1], i_borderRadius[1]));
    float bottomRightDst = distance(i_textureCoordinates, vec2(1.0 - i_borderRadius[2]));
    float bottomLeftDst = distance(i_textureCoordinates, vec2(i_borderRadius[3], 1.0 - i_borderRadius[3]));

    // Top left
    result = mix(result, hide,
                 step(i_borderRadius[0], topLeftDst) *
                 step(i_textureCoordinates.x, i_borderRadius[0]) *
                 step(i_textureCoordinates.y, i_borderRadius[0])
             );
    // Top right
    result = mix(result, hide,
                 step(i_borderRadius[1], topRightDst) *
                 step(1.0 - i_borderRadius[1], i_textureCoordinates.x) *
                 step(i_textureCoordinates.y, i_borderRadius[1])
             );
    // Bottom right
    result = mix(result, hide,
                 step(i_borderRadius[2], bottomRightDst) *
                 step(1.0 - i_borderRadius[2], i_textureCoordinates.x) *
                 step(1.0 - i_borderRadius[2], i_textureCoordinates.y)
             );
    // Bottom left
    result = mix(result, hide,
                 step(i_borderRadius[3], bottomLeftDst) *
                 step(i_textureCoordinates.x, i_borderRadius[3]) *
                 step(1.0 - i_borderRadius[3], i_textureCoordinates.y)
             );

    return result;
}

void main() {
    vec4 borderColor = getBorderColor();
    vec4 borderRadius = getBorderRadius();

    o_color = mix(i_color, borderColor, borderColor.a);
    o_color *= getBorderRadius();
}
