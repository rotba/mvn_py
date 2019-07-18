package p_1;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class AssafTest {

    Assaf a = new Assaf();
    @Test
    void moo() {
    }
    @Test
    void goo() {
    }
    @Test
    void compTest() {
        assertEquals(a.moo(), 6);
    }
    @Test
    void notCompTest() {
        assertEquals(a.notComp(), 6);
    }
}