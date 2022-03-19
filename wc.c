#include <math.h>
#include <pango/pangocairo.h>
#include <stdlib.h>
#include <time.h>
#include <fontconfig/fontconfig.h>

static int random_int(int start, int end) {
    static int first = 1;
    if(first) {
        srand(time(NULL));
        first = 0;
    }
    if(start == end) {
        return start;
    }

    return start + ((rand() - start)%(end-start));
}

int query_location(int* sum, int w, int h, int x, int y, int space_w, int space_h) {
    int area = sum[y*w + x] + sum[(y+space_h)*w + x + space_w];
    area -= sum[(y+space_h)*w + x] + sum[y*w + x + space_w];
    return area;
}

int get_space(int* sum, int w, int h, int space_w, int space_h, int* out_x, int* out_y) {
    int area, x, y;

    //first just guess randomly (more efficient early on)
    for(int d = 0; d < 1000; d++) {
        y = random_int(0, h - space_h);
        x = random_int(0, w - space_w);
        area = query_location(sum, w, h, x, y, space_w, space_h);
        if(area == 0) {
            *out_x = x;
            *out_y = y;
            return 0;
        }
    }

    //resort to exhaustive search
    for(y = 0; y < h - space_h; y++) {
        for(x = 0; x < w - space_w; x++) {
            area = query_location(sum, w, h, x, y, space_w, space_h);
            if(area == 0) {
                *out_x = x;
                *out_y = y;
                return 0;
            }
        }
    }

    return -1;
}

void perform_sum(uint8_t* data, int w, int h, int* sum) {
    for(int y = 0; y < h; y++) {
        for(int x = 0; x < w; x++) {
            sum[y*w + x] = data[y*w + x];
            if(y > 0)
                sum[y*w + x] += sum[(y-1)*w + x];
            if(x > 0)
                sum[y*w + x] += sum[y*w + x - 1];
            if(y > 0 && x > 0)
                sum[y*w + x] -= sum[(y-1)*w + x - 1];
        }
    }
}

void load_font(char* path) {
    FcConfigAppFontAddFile(FcConfigGetCurrent(), path);
}

void path_text(cairo_t *cr, char* text, int size, char* family) {
    PangoLayout *layout;
    PangoFontDescription *desc;
    PangoRectangle extents;

    layout = pango_cairo_create_layout(cr);

    desc = pango_font_description_from_string(family);
    pango_font_description_set_absolute_size(desc, (double)size * PANGO_SCALE);
    pango_layout_set_font_description(layout, desc); 
    pango_font_description_free(desc);

    pango_layout_set_text(layout, text, -1);
    pango_layout_get_pixel_extents(layout, &extents, NULL);

    cairo_rel_move_to(cr, -extents.x, -extents.y);
    pango_cairo_layout_path(cr, layout);
 
    g_object_unref (layout);
}

void get_text_extent(cairo_t *cr, char* text, int size, char* family, int* w, int* h, int* x, int* y) {
    PangoLayout *layout;
    PangoFontDescription *desc;
    PangoRectangle extents;

    layout = pango_cairo_create_layout(cr);

    desc = pango_font_description_from_string(family);
    pango_font_description_set_absolute_size(desc, (double)size * PANGO_SCALE);
    pango_layout_set_font_description(layout, desc);
    pango_font_description_free(desc);

    pango_layout_set_text(layout, text, -1);
    pango_layout_get_pixel_extents(layout, &extents, NULL);

    *w = extents.width;
    *h = extents.height;
    *x = extents.x;
    *y = extents.y;

    g_object_unref (layout);
}