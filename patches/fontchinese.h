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

#ifndef SCI_GRAPHICS_FONTCHINESE_H
#define SCI_GRAPHICS_FONTCHINESE_H

#include "common/array.h"
#include "common/hashmap.h"
#include "sci/graphics/scifont.h"

namespace Graphics {
class Big5Font;
}

namespace Sci {

/**
 * Traditional Chinese (Big5) font wrapper for SCI games.
 *
 * Wraps the game's original SCI font resource for single-byte (ASCII) glyphs,
 * and renders double-byte Big5 sequences via ScummVM's shared Graphics::Big5Font.
 * Selected in GfxCache::getFont when the game language is Common::ZH_TWN.
 *
 * This mirrors the low-res Big5 rendering approach used by the sherlock/darkseed
 * engines (16px-wide glyphs drawn straight into the SCI screen), rather than the
 * PC-98/Korean hi-res gfx-driver path.
 */
class GfxFontChinese : public GfxFont {
public:
	GfxFontChinese(ResourceManager *resMan, GfxScreen *screen, GuiResourceId resourceId);
	~GfxFontChinese() override;

	GuiResourceId getResourceId() override;
	byte getHeight() override;
	bool isDoubleByte(uint16 chr) override;
	byte getCharWidth(uint16 chr) override;
	byte getCharHeight(uint16 chr) override;
	void draw(uint16 chr, int16 top, int16 left, byte color, bool greyedOutput) override;

private:
	// Hi-res Big5 draw for ZH_TWN 640x400 upscale: draws a 32xN glyph straight onto the
	// display buffer so strokes stay sharp instead of blocky 2x-nearest. See drawHiRes().
	bool loadHiResFont();
	void drawHiRes(uint16 point, int16 top, int16 left, byte color);

	GfxScreen *_screen;
	GuiResourceId _resourceId;
	GfxFontFromResource *_asciiFont; // original SCI font, for single-byte glyphs
	Graphics::Big5Font *_big5;       // shared Traditional Chinese bitmap font (low-res 16px)
	int _big5Height;

	// Hi-res font (own format, not Graphics::Big5Font which is fixed 16px): each glyph is
	// _hiH rows x (_hiW/8) bytes, keyed by big-endian Big5 code -> offset into _hiData.
	Common::HashMap<uint16, uint32> _hiIndex;
	Common::Array<byte> _hiData;
	int _hiW, _hiH;
};

} // End of namespace Sci

#endif // SCI_GRAPHICS_FONTCHINESE_H
