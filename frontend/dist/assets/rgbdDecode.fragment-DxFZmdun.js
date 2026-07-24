import{S as r}from"./sindarius-gcodeviewer.es-MXC-9r8X.js";import"./helperFunctions-BY-a1NO1.js";import"./index-CVVzMZLJ.js";import"./react-vendor-9t-2b6dQ.js";import"./icons-n1Rr91tl.js";const e="rgbdDecodePixelShader",o=`varying vec2 vUV;uniform sampler2D textureSampler;
#include<helperFunctions>
#define CUSTOM_FRAGMENT_DEFINITIONS
void main(void) 
{gl_FragColor=vec4(fromRGBD(texture2D(textureSampler,vUV)),1.0);}`;r.ShadersStore[e]||(r.ShadersStore[e]=o);const S={name:e,shader:o};export{S as rgbdDecodePixelShader};
