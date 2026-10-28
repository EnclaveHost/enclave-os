#include "app/streaming/audio/renderers/audioqueuebudget.h"
#include <cassert>
#include <climits>
#include <cstdio>

int main() {
    // 48 kHz stereo signed-16 audio: 192 bytes/ms; each frame is 5 ms.
    assert(audioFitsBudget(50*192, 5*192, 5*192, 5, 25));
    assert(!audioFitsBudget(50*192+1, 5*192, 5*192, 5, 25));
    assert(audioFitsBudget(0, 5*192, 5*192, 5, 75));
    assert(!audioFitsBudget(0, 5*192, 5*192, 5, 76));
    assert(!audioFitsBudget(0, -1, 960, 5, 0));
    assert(!audioFitsBudget(0, 960, 0, 5, 0));
    assert(!audioFitsBudget(0, 960, 960, 0, 0));
    assert(!audioFitsBudget(0, 0, 960, 81, 0));
    assert(!audioFitsBudget(0, 0, 960, 5, 81));
    assert(!audioFitsBudget(UINT_MAX, INT_MAX, 960, 5, 0));
    for (unsigned pending = 0; pending <= 80; ++pending) {
        unsigned remaining = (80-pending)*192;
        assert(audioFitsBudget(remaining, 0, 960, 5, pending));
        assert(!audioFitsBudget(remaining+1, 0, 960, 5, pending));
    }
    puts("PASS: combined backlog, partial frames, invalid inputs and overflow bounds");
}
