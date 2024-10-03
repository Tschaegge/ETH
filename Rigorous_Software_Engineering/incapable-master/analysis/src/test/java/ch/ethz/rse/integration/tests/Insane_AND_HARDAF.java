
package ch.ethz.rse.integration.tests;
// DISABLED
import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE UNSAFE
// FITS_IN_TROLLEY UNSAFE
// FITS_IN_RESERVE SAFE

public class Insane_AND_HARDAF {
  public static void m1(int j){
    Store s = new Store(1, 10);
    int l = 1182;
    if (j < 0 && l -1 == 1181) {
      s.get_delivery(j);
    }
    if (j > 0 || j <= 0) {
      s.get_delivery(2);
    }
 }
}

