
package ch.ethz.rse.integration.tests;

import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE SAFE
// FITS_IN_TROLLEY UNSAFE
// FITS_IN_RESERVE SAFE

public class paratest {

  public static void m1(int j) {
    Store s = new Store(2, 4);
    //j = j + 1;
    s.get_delivery(3);
    
  }
}