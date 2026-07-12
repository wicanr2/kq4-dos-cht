/* ScummVM - Graphic Adventure Engine
 *
 * ScummVM is the legal property of its developers, whose names
 * are too numerous to list here. Please refer to the COPYRIGHT
 * file distributed with this source distribution.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

#include "common/file.h"
#include "graphics/big5.h"

#include "sci/sci.h"
#include "sci/graphics/screen.h"
#include "sci/graphics/fontchinese.h"

namespace Sci {

// Big5 font data file shipped alongside the game (part of the CHT patch).
static const char *kChineseFontFile = "qfg1_big5.fnt";
// Layout advance per Chinese char (logical 320x200 px). Reduced from the Big5Font native
// 16px so dialogue fits KQ4's compact portrait/message boxes without overflowing (issue #1).
static const int kBig5Width = 14;

// Hi-res Big5 font (own format, bake_hires_font.py): 32px-wide, kHiH-row glyphs drawn
// straight onto the 640x400 display buffer for sharp strokes under ZH_TWN upscaling.
static const char *kChineseHiResFontFile = "qfg1_big5_hi.fnt";
static const int kHiW = 24;   // 2x the 12px logical glyph; drawn centered in the 14px cell
static const int kHiH = 22;

GfxFontChinese::GfxFontChinese(ResourceManager *resMan, GfxScreen *screen, GuiResourceId resourceId)
	: _screen(screen), _resourceId(resourceId), _big5(nullptr), _big5Height(14) {
	// Original SCI font for single-byte (ASCII / control) glyphs.
	_asciiFont = new GfxFontFromResource(resMan, screen, resourceId);

	Common::File fontFile;
	if (fontFile.open(kChineseFontFile)) {
		_big5 = new Graphics::Big5Font();
		_big5->loadPrefixedRaw(fontFile, _big5Height);
		_big5Height = _big5->getFontHeight();
	} else {
		warning("GfxFontChinese: could not open '%s'; Chinese glyphs will be blank", kChineseFontFile);
	}
	// Line-height metric for layout (getHeight). Capped below the native glyph height so lines
	// pack tighter and boxes hold more text (issue #1: 對話後面被截斷). The hi-res glyph (kHiH)
	// is the actual drawn height; low-res is only a rare fallback under ZH_TWN (always upscaled).
	if (_big5Height > 13)
		_big5Height = 13;

	_hiW = kHiW;
	_hiH = kHiH;
	loadHiResFont();
}

// Load the hi-res Big5 font: repeated { big-endian Big5 code (uint16), _hiH*(_hiW/8) glyph
// bytes }, terminated by 0xFFFF. Keeps a code->offset index into the flat _hiData blob.
// Missing file just means we fall back to the low-res Big5 path (no hi-res sharpening).
bool GfxFontChinese::loadHiResFont() {
	Common::File f;
	if (!f.open(kChineseHiResFontFile))
		return false;
	const uint bytesPerGlyph = _hiH * (_hiW / 8);
	while (!f.eos()) {
		uint16 code = f.readUint16BE();
		if (f.eos() || code == 0xFFFF)
			break;
		uint32 offset = _hiData.size();
		_hiData.resize(offset + bytesPerGlyph);
		if (f.read(&_hiData[offset], bytesPerGlyph) != bytesPerGlyph)
			break;
		_hiIndex[code] = offset;
	}
	return !_hiIndex.empty();
}

GfxFontChinese::~GfxFontChinese() {
	delete _big5;
	delete _asciiFont;
}

GuiResourceId GfxFontChinese::getResourceId() {
	return _resourceId;
}

byte GfxFontChinese::getHeight() {
	byte asciiHeight = _asciiFont->getHeight();
	return MAX<byte>(asciiHeight, (byte)_big5Height);
}

// text16 tests this on the first (lead) byte before combining the pair.
bool GfxFontChinese::isDoubleByte(uint16 chr) {
	return (chr >= 0x81) && (chr <= 0xFE);
}

byte GfxFontChinese::getCharWidth(uint16 chr) {
	// chr may arrive either as a bare lead byte (during width scans) or as a
	// combined lead|(trail<<8) value (during drawing). Both mean a Big5 char.
	if (chr > 0xFF || isDoubleByte(chr))
		return kBig5Width;
	return _asciiFont->getCharWidth(chr);
}

byte GfxFontChinese::getCharHeight(uint16 chr) {
	if (chr > 0xFF || isDoubleByte(chr))
		return (byte)_big5Height;
	return _asciiFont->getHeight();
}

void GfxFontChinese::draw(uint16 chr, int16 top, int16 left, byte color, bool greyedOutput) {
	// Single-byte: delegate to the original SCI font (keeps ASCII pixel-identical).
	if (chr <= 0xFF) {
		_asciiFont->draw(chr, top, left, color, greyedOutput);
		return;
	}

	// Double-byte: chr == lead | (trail << 8); Big5Font wants (lead << 8) | trail.
	uint16 point = ((chr & 0xFF) << 8) | (chr >> 8);

	// Hi-res path: when ZH_TWN runs upscaled (640x400 display) and we have a hi-res glyph,
	// draw sharp 32xN strokes directly onto the display instead of the blocky 2x low-res.
	if (_screen->getDisplayWidth() > _screen->getWidth() && _hiIndex.contains(point)) {
		drawHiRes(point, top, left, color);
		return;
	}

	byte glyph[kBig5Width * 16];
	memset(glyph, 0, sizeof(glyph));
	bool drawn = false;
	if (_big5)
		drawn = _big5->drawBig5Char(glyph, point, kBig5Width, _big5Height, kBig5Width,
		                            /*color*/ 1, /*outlineColor*/ 0, /*outline*/ false, /*bpp*/ 1);
	if (!drawn) {
		// Fall back to a placeholder so missing glyphs are visible, not silent.
		_asciiFont->draw('?', top, left, color, greyedOutput);
		return;
	}

	uint16 screenWidth = _screen->fontIsUpscaled() ? _screen->getDisplayWidth() : _screen->getWidth();
	uint16 screenHeight = _screen->fontIsUpscaled() ? _screen->getDisplayHeight() : _screen->getHeight();

	for (int y = 0; y < _big5Height; y++) {
		for (int x = 0; x < kBig5Width; x++) {
			if (!glyph[y * kBig5Width + x])
				continue;
			int screenX = left + x;
			int screenY = top + y;
			if (0 <= screenX && screenX < screenWidth && 0 <= screenY && screenY < screenHeight)
				_screen->putFontPixel(top, screenX, y, color);
		}
	}
}

// Draw a hi-res Big5 glyph directly onto the 640x400 display buffer. The game positions
// text in logical 320x200 coords, so we map (left, top) -> (left*2, top*2) on the display
// and toggle _fontIsUpscaled so putFontPixel writes straight to the display (no further
// nearest-scale), giving sharp 32xN strokes. ASCII glyphs are unaffected (they draw with
// _fontIsUpscaled == false and get the normal 2x upscale, matching the game art).
void GfxFontChinese::drawHiRes(uint16 point, int16 top, int16 left, byte color) {
	Common::HashMap<uint16, uint32>::const_iterator it = _hiIndex.find(point);
	if (it == _hiIndex.end())
		return;
	const byte *bmp = &_hiData[it->_value];
	const int rowBytes = _hiW / 8;
	// Centre the (possibly narrower) hi-res glyph within the 2x logical advance cell.
	const int dispLeft = left * 2 + (2 * kBig5Width - _hiW) / 2;
	const int dispTop = top * 2;
	const int dispW = _screen->getDisplayWidth();
	const int dispH = _screen->getDisplayHeight();

	const bool savedUpscaled = _screen->fontIsUpscaled();
	_screen->setFontIsUpscaled(true);
	for (int gy = 0; gy < _hiH; gy++) {
		const int dispY = dispTop + gy;
		if (dispY < 0 || dispY >= dispH)
			continue;
		for (int gx = 0; gx < _hiW; gx++) {
			if (!(bmp[gy * rowBytes + (gx >> 3)] & (0x80 >> (gx & 7))))
				continue;
			const int dispX = dispLeft + gx;
			if (dispX < 0 || dispX >= dispW)
				continue;
			_screen->putFontPixel(dispTop, dispX, gy, color);
		}
	}
	_screen->setFontIsUpscaled(savedUpscaled);
}

} // End of namespace Sci
