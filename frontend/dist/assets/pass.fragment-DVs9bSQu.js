import{S as r}from"./sindarius-gcodeviewer.es-B_xu1QnT.js";import"./index-BA7oqd8V.js";import"./react-vendor-9t-2b6dQ.js";import"./icons-CNFEcl-l.js";const e="passPixelShader",o=`varying vec2 vUV;uniform sampler2D textureSampler;
#define CUSTOM_FRAGMENT_DEFINITIONS
void main(void) 
{gl_FragColor=texture2D(textureSampler,vUV);}`;r.ShadersStore[e]||(r.ShadersStore[e]=o);const s={name:e,shader:o};export{s as passPixelShader};
