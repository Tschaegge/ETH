
package ch.ethz.rse.integration.tests;

import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE SAFE
// FITS_IN_TROLLEY UNSAFE
// FITS_IN_RESERVE SAFE

public class Test_Assign_Store_Copy {

  public static void m1() {
    Store s1 = new Store(2, 4);
    
    Store s2 = new Store(2, 2);

    s2.get_delivery(2);

    s2 = s1;

    s2.get_delivery(3);
  }
}
