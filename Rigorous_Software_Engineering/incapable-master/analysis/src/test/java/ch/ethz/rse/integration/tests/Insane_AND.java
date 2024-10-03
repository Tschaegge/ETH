
package ch.ethz.rse.integration.tests;

import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE SAFE
// FITS_IN_TROLLEY UNSAFE
// FITS_IN_RESERVE SAFE

public class Insane_AND {
  public static void m1(){
    Store s = new Store(1, 10);
    int dölf = 12;
    int nice = 69;
    if (12 * dölf == 144 && nice - 10 == 59) {
      s.get_delivery(2);
    }
 }
}

