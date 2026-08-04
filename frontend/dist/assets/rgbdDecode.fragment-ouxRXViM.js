import{S as r}from"./sindarius-gcodeviewer.es-DDimEmKV.js";import"./helperFunctions-CzwHTACi.js";import"./index-B5yfkrT0.js";import"./react-vendor-9t-2b6dQ.js";import"./icons-CNFEcl-l.js";const e="rgbdDecodePixelShader",o=`varying vec2 vUV;uniform sampler2D textureSampler;
#include<helperFunctions>
#define CUSTOM_FRAGMENT_DEFINITIONS
void main(void) 
{gl_FragColor=vec4(fromRGBD(texture2D(textureSampler,vUV)),1.0);}`;r.ShadersStore[e]||(r.ShadersStore[e]=o);const S={name:e,shader:o};export{S as rgbdDecodePixelShader};
