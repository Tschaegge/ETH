
package ch.ethz.rse.integration.tests;

import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE SAFE
// FITS_IN_TROLLEY SAFE
// FITS_IN_RESERVE UNSAFE

public class Insane_Store_For_Crazy {
  public static void m1(int j){
    Store s = new Store(1, 5);

    for (int i = ((12 * 12) * 1) + (0*j); i < 150; i++) {
      s.get_delivery(1);
    }

    
   }
 }

