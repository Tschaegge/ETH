
package ch.ethz.rse.integration.tests;

import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE SAFE
// FITS_IN_TROLLEY UNSAFE
// FITS_IN_RESERVE UNSAFE

public class Insane_Store_For {
  public static void m1(int j){
    Store s = new Store(3, 1000);
    for (int i = 0; i < j; i++) {
        s = new Store(1,2);
        s.get_delivery(1);
    }

    s.get_delivery(2);
    
   }
 }

