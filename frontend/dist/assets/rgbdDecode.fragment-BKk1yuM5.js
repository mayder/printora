import{S as r}from"./sindarius-gcodeviewer.es-B_xu1QnT.js";import"./helperFunctions-MjV_PV-p.js";import"./index-BA7oqd8V.js";import"./react-vendor-9t-2b6dQ.js";import"./icons-CNFEcl-l.js";const e="rgbdDecodePixelShader",o=`varying vec2 vUV;uniform sampler2D textureSampler;
#include<helperFunctions>
#define CUSTOM_FRAGMENT_DEFINITIONS
void main(void) 
{gl_FragColor=vec4(fromRGBD(texture2D(textureSampler,vUV)),1.0);}`;r.ShadersStore[e]||(r.ShadersStore[e]=o);const S={name:e,shader:o};export{S as rgbdDecodePixelShader};
