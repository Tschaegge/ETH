
package ch.ethz.rse.integration.tests;

import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE SAFE
// FITS_IN_TROLLEY SAFE
// FITS_IN_RESERVE SAFE

public class Basic_Unreachable_Test {

  public static void m1() {
    Store s = new Store(2, 4);
    
    int a = 2 * 3;
    if(a<5){
      s.get_delivery(a);
    }

    s.get_delivery(2);
  }
}