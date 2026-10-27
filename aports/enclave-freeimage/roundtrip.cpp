#include <FreeImage.h>
#include <cassert>
#include <cstdio>
#include <cstdint>
int main() {
    FreeImage_Initialise();
    FIBITMAP *half = FreeImage_AllocateT(FIT_RGBA16F, 2, 2);
    assert(half && FreeImage_GetImageType(half) == FIT_RGBA16F);
    auto *pixel = reinterpret_cast<uint16_t *>(FreeImage_GetScanLine(half, 0));
    pixel[0] = 0x3c00; pixel[1] = 0; pixel[2] = 0; pixel[3] = 0x3c00;
    FIBITMAP *full = FreeImage_ConvertToRGBAF(half);
    assert(full);
    auto *rgba = reinterpret_cast<FIRGBAF *>(FreeImage_GetScanLine(full, 0));
    assert(rgba->red == 1.f && rgba->green == 0.f && rgba->blue == 0.f && rgba->alpha == 1.f);
    FIBITMAP *bitmap = FreeImage_Allocate(2, 2, 24);
    assert(bitmap);
    RGBQUAD color = {}; color.rgbRed = 123; color.rgbGreen = 45; color.rgbBlue = 67;
    assert(FreeImage_SetPixelColor(bitmap, 0, 0, &color));
    FIMEMORY *stream = FreeImage_OpenMemory();
    assert(stream && FreeImage_SaveToMemory(FIF_PNG, bitmap, stream));
    assert(FreeImage_SeekMemory(stream, 0, SEEK_SET));
    FIBITMAP *loaded = FreeImage_LoadFromMemory(FIF_PNG, stream);
    RGBQUAD result = {};
    assert(loaded && FreeImage_GetPixelColor(loaded, 0, 0, &result));
    assert(result.rgbRed == 123 && result.rgbGreen == 45 && result.rgbBlue == 67);
    FreeImage_Unload(loaded); FreeImage_Unload(bitmap); FreeImage_CloseMemory(stream);
    FreeImage_Unload(full); FreeImage_Unload(half); FreeImage_DeInitialise();
}
