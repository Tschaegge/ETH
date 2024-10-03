
package ch.ethz.rse.integration.tests;

import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE SAFE
// FITS_IN_TROLLEY SAFE
// FITS_IN_RESERVE UNSAFE

public class Insane_Multiple_Args {
  public static void m1(int j, int k, int l){
    Store s = new Store(1, 5);
    for (int i = 0; i < 5; i++) {
      if (i < j) {
        s.get_delivery(1);
      }
      if (i<k) {
        s.get_delivery(1);
      }
    }
  
   }
 }

