#include <FreeImage.h>
#include <cassert>
#include <cstdio>
#include <cstdint>
int main() {
    FreeImage_Initialise();
    FIBITMAP *full = FreeImage_AllocateT(FIT_RGBAF, 2, 2);
    assert(full);
    for (int y = 0; y < 2; ++y) {
        auto *rgba = reinterpret_cast<FIRGBAF *>(FreeImage_GetScanLine(full, y));
        for (int x = 0; x < 2; ++x) rgba[x] = {1.f, 0.f, 0.f, 1.f};
    }
    FIMEMORY *exr = FreeImage_OpenMemory();
    assert(exr && FreeImage_SaveToMemory(FIF_EXR, full, exr));
    assert(FreeImage_SeekMemory(exr, 0, SEEK_SET));
    FIBITMAP *half = FreeImage_LoadFromMemory(FIF_EXR, exr, EXR_ALLOW_FOR_FP16);
    assert(half && FreeImage_GetImageType(half) == FIT_RGBA16F);
    auto *pixel = reinterpret_cast<uint16_t *>(FreeImage_GetScanLine(half, 0));
    assert(pixel[0] == 0x3c00 && pixel[1] == 0 && pixel[2] == 0 && pixel[3] == 0x3c00);
    FreeImage_CloseMemory(exr);
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
