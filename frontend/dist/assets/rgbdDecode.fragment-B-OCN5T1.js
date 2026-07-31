import{S as r}from"./sindarius-gcodeviewer.es-BkGI4vcO.js";import"./helperFunctions-_EW08Jr6.js";import"./index-DzyWAtRQ.js";import"./react-vendor-9t-2b6dQ.js";import"./icons-DljbX5Dz.js";const e="rgbdDecodePixelShader",o=`varying vec2 vUV;uniform sampler2D textureSampler;
#include<helperFunctions>
#define CUSTOM_FRAGMENT_DEFINITIONS
void main(void) 
{gl_FragColor=vec4(fromRGBD(texture2D(textureSampler,vUV)),1.0);}`;r.ShadersStore[e]||(r.ShadersStore[e]=o);const S={name:e,shader:o};export{S as rgbdDecodePixelShader};
